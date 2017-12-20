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


def _get_spec_path(api_level, extension):
    return os.path.join(defaults.CONFIG_DIRECTORY,
                        '{}.{}'.format(api_level, extension))


def _is_spec_exists(api_level, extension):
    return os.path.exists(_get_spec_path(api_level, extension))


def _load_yaml_spec(api_level):
    spec_url = "{0}://{1}/api/{2}.{3}.yml".format(settings.API_SCHEME,
                                                  settings.API_HOST,
                                                  api_level,
                                                  settings.API_VERSION)
    try:
        resp = requests.get(spec_url, verify=settings.SSL_VERIFY_PEER)
    except requests.exceptions.SSLError as e:
        import ssl
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
    text = None
    if os.path.exists(spec_path):
        with open(spec_path, "r") as fp:
            text = fp.read()
    return text


def _write_spec(spec_path, text):
    with open(spec_path, "w") as fp:
        fp.write(text)


def _update_spec(api_level):
    """
    Downloads yaml spec and converts it to JSON
    Both files are stored in configuration directory.
    """

    try:
        yaml_spec_text = _load_yaml_spec(api_level)
        if not yaml_spec_text:
            raise Exception('Can\'t load spec file')

        try:
            struct = yaml.load(yaml_spec_text)
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
        return False, e.message or 'Unknown reason'


class UpdateScalrCTL(commands.BaseAction):

    def run(self, *args, **kwargs):
        update()

    def get_description(self):
        return "Fetch new API specification if available."


def is_update_required():
    """
    Determine if spec update is needed.
    """

    # prevent from running 'update' more than once
    if 'update' in sys.argv:
        return False
    else:
        exists = [_is_spec_exists(api, 'yaml') and
                  _is_spec_exists(api, 'json') for api in defaults.API_LEVELS]
        return not all(exists)


def update():
    """
    Update spec for all available APIs.
    """

    amount = len(defaults.API_LEVELS)

    for index, api_level in enumerate(defaults.API_LEVELS, 1):

        click.echo('[{}/{}] Updating specifications for {} API ... '
                   .format(index, amount, api_level), nl=False)

        with utils._spinner():
            success, fail_reason = _update_spec(api_level)

        if success:
            click.secho('Done', fg='green')
        else:
            click.secho('Failed: {}'.format(fail_reason), fg='red')

