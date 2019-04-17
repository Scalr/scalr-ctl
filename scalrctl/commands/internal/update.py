# -*- coding: utf-8 -*-
import os
import sys
import json
import traceback

import six
import yaml
import requests

from scalrctl import click, defaults, settings, commands, utils

__author__ = 'Dmitriy Korsakov, Sergey Babak'

NOUPDATE_FLAG_PATH = os.path.join(defaults.CONFIG_DIRECTORY, '.noupdate')


def _get_spec_path(api_level, extension):
    """
    Return path of determine specification.

    :rtype: str
    """
    return os.path.join(defaults.CONFIG_DIRECTORY,
                        '{}.{}'.format(api_level, extension))


def _is_spec_exists(api_level, extension):
    """
    Check if specifications path exist.

    :rtype: bool
    """
    return os.path.exists(_get_spec_path(api_level, extension))


def _fetch_yaml_spec(api_level):
    '''
    Fetch spec file from API server.

    :param api_level: system, user, account, global, openapi
    :return:
    '''
    spec_url = "{0}://{1}/api/{2}.{3}.yml".format(settings.API_SCHEME,
                               settings.API_HOST,
                               api_level,
                               settings.API_VERSION)
    try:
        resp = requests.get(spec_url, verify=settings.SSL_VERIFY_PEER)
    except requests.exceptions.SSLError as e:
        if 'CertificateError' in str(e):
            sni_supported = None
            try:
                from OpenSSL._util import lib as _lib
                if _lib.Cryptography_HAS_TLSEXT_HOSTNAME:
                    sni_supported = True
            except ImportError:
                sni_supported = False
            if not sni_supported:
                errmsg = "\nError: Your Python version %s does not support SNI. " \
                         "This can be resolved by upgrading Python to version 2.7.9 or " \
                         "by installing pyOpenSSL>=17.3.0. More info in Requests FAQ: " \
                         "http://docs.python-requests.org/en/master/community/faq/#what-are-hostname-doesn-t-match-errors" \
                         " \nIf you are having problems installing pyOpenSSL try to upgrade pip first." % sys.version[:5]
                click.echo(errmsg)
                sys.exit()
    return resp.text if resp.status_code == 200 else None


def _read_spec(spec_path):
    """
    Read specification via determine path.

    :param str spec_path: path to specification
    :rtype str
    """
    text = None
    if os.path.exists(spec_path):
        with open(spec_path, "r") as fp:
            text = fp.read()
    return text


def _write_spec(spec_path, text):
    """
    Write data into specification.

    :param str spec_path: path to specification
    :param str text:
    :rtype:
    """
    with open(spec_path, "w") as fp:
        fp.write(text)


def _update_spec(api_level):
    """
    Downloads yaml spec and converts it to JSON
    Both files are stored in configuration directory.
    """
    try:
        yaml_spec_text = _fetch_yaml_spec(api_level)
        if not yaml_spec_text:
            raise Exception('Can\'t load spec file')

        try:
            struct = yaml.safe_load(yaml_spec_text)
            json_spec_text = json.dumps(struct)
        except (KeyError, TypeError, yaml.YAMLError) as e:
            six.reraise(type(e), "Swagger specification is not valid:\n{}"
                        .format(traceback.format_exc()))

        yaml_spec_path = _get_spec_path(api_level, 'yaml')
        json_spec_path = _get_spec_path(api_level, 'json')

        old_yaml_spec_text = _read_spec(yaml_spec_path)

        # update yaml spec
        if yaml_spec_text != old_yaml_spec_text:
            _write_spec(yaml_spec_path, yaml_spec_text)

        # update json spec and routes
        _write_spec(json_spec_path, json_spec_text)

        return True, None
    except Exception as e:
        return False, str(e) or 'Unknown reason'


class UpdateScalrCTL(commands.BaseAction):

    def run(self, *args, **kwargs):
        update()

    def get_description(self):
        return "Fetch new API specification if available."


def _check_update():
    """
    Check if update is needed.

    :rtype: bool
    """
    if 'update' in sys.argv or 'configure' in sys.argv or os.path.exists(NOUPDATE_FLAG_PATH):
        return False
    return True


def _is_openapi_v2_update_required():
    """
    Determine if OpenAPI v2 update is needed.

    :rtype: bool
    """
    # prevent from running 'update' more than once
    if not _check_update():
        return False
    return not all(
        _is_spec_exists(level, 'yaml') and _is_spec_exists(level, 'json')
        for level in defaults.API_LEVELS)


def _is_openapi_v3_update_required():
    """
    Determine if OpenAPI v3 update is needed.

    :rtype: bool
    """
    # prevent from running 'update' more than once
    if not _check_update():
        return False
    return not (_is_spec_exists('openapi', 'yaml') and _is_spec_exists('openapi', 'json'))


def _is_openapi_update_required():
    """
    Determine if OpenAPI specification update is needed.

    :rtype: bool
    """
    return _is_openapi_v3_update_required() or _is_openapi_v2_update_required()


def _update_openapi_v2():
    """
    Update OpenAPI v2 specification.

    :return bool: `True` if spec has been updated successfully, otherwise `False`.
    """
    any_failed = False
    for index, api_level in enumerate(defaults.API_LEVELS, 1):
        click.echo((
            "[{}/{}] Updating specifications for Scalr {} API (Swagger)..."
        ).format(index, len(defaults.API_LEVELS), api_level), nl=False)
        with utils.Spinner():
            success, fail_reason = _update_spec(api_level)
        if success:
            click.secho("Done", fg='green')
        else:
            click.secho("Failed: {}".format(fail_reason), fg='red')
            any_failed = True
    return not any_failed


def _update_openapi_v3():
    """
    Update OpenAPI v3 specification.

    :return bool: `True` if spec has been updated successfully, otherwise `False`.
    """
    click.echo("Updating specification for Scalr API (OpenAPI)... ", nl=False)
    with utils.Spinner():
        success, fail_reason = _update_spec("openapi")
    if success:
        click.secho("Done", fg='green')
        return True
    click.secho("Failed: {}".format(fail_reason), fg='red')
    return False


def update(force=True):
    """
    Update OpenAPI v3 or/and v2 specification (json and yaml).

    :param bool force: Update specification forcefully (default=True).
    """
    if os.path.exists(NOUPDATE_FLAG_PATH):
        if force:
            click.secho((
                "Update is disabled by user. To enable remove {path}"
            ).format(path=NOUPDATE_FLAG_PATH), fg='yellow')
        return
    if not _is_openapi_update_required() and not force:
        return

    if not _update_openapi_v3():
        click.secho("OpenAPI spec is not available.", fg='yellow')
        _update_openapi_v2()
