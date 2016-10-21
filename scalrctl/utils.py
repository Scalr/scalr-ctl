# -*- coding: utf-8 -*-
import os
import json
import yaml
import traceback

from scalrctl import click, defaults, settings


def read_spec(api_level, ext='json'):
    """
    Reads Scalr specification file, json or yaml.
    """

    spec_path = os.path.join(defaults.CONFIG_DIRECTORY,
                             '{}.{}'.format(api_level, ext))

    if os.path.exists(spec_path):
        with open(spec_path, 'r') as fp:
            spec_data = fp.read()

        if ext == 'json':
            return json.loads(spec_data)
        elif ext == 'yaml':
            return yaml.safe_load(spec_data)
    else:
        msg = "Scalr specification file '{}' does  not exist, " \
              "try to run 'scalr-ctl update'.".format(spec_path)
        raise click.ClickException(msg)


def read_routes():
    if os.path.exists(defaults.ROUTES_PATH):
        with open(defaults.ROUTES_PATH, 'r') as fp:
            api_routes = fp.read()
        return json.loads(api_routes)


def read_scheme():
    with open(os.path.join(os.path.dirname(__file__),
                           'scheme/scheme.json')) as fp:
        return json.load(fp)


def read_config(profile=None):
    confpath = os.path.join(
        defaults.CONFIG_DIRECTORY,
        '{}.yaml'.format(profile)
    ) if profile else defaults.CONFIG_PATH

    if os.path.exists(confpath):
        with open(confpath, 'r') as fp:
            return yaml.load(fp)


def debug(msg):
    if settings.debug_mode:
        click.secho("DEBUG: {}".format(msg),
                    fg='green' if settings.colored_output else None)


def reraise(message):
    debug(traceback.format_exc())
    message = str(message)
    if not settings.debug_mode:
        message = "{}, use '--debug' option for details.".format(message)
    raise click.ClickException(message)
