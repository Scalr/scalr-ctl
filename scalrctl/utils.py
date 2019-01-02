# -*- coding: utf-8 -*-
import os
import sys
import json
import yaml
import time
import itertools
import threading
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


def read_spec_openapi():
    """
    Reads Scalr specification file, json or yaml.
    """

    spec_path = os.path.join(defaults.CONFIG_DIRECTORY, 'openapi.json')

    if os.path.exists(spec_path):
        with open(spec_path, 'r') as fp:
            spec_data = fp.read()

        return json.loads(spec_data)
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
    with open(defaults.SCHEME_PATH) as fp:
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
    import sys
    exc_info = sys.exc_info()
    if isinstance(exc_info[1], click.ClickException):
        exc_class = exc_info[0]
    else:
        exc_class = click.ClickException
    debug(traceback.format_exc())
    message = str(message)
    if not settings.debug_mode:
        message = "{}\nUse '--debug' option for details.".format(message)
    raise exc_class(message)


def is_openapi_v3(data):
    if "openapi" in data:
        return True
    elif "basePath" in data:
        return False


def lookup(response_ref, raw_spec):
    """
    Returns document section
    Example: #/definitions/Image returns Image defenition section.
    """
    if response_ref.startswith('#'):
        paths = response_ref.split('/')[1:]
        result = raw_spec
        for path in paths:
            if path not in result:
                return
            result = result[path]
        return result


def merge_all(data, raw_spec):
    merged = {}

    if "allOf" not in data:
        #raise MultipleClickException("Invalid spec data: Cannot merge object scpec block: %s" % data)
        return data

    data = data['allOf']
    for block in data:
        if "$ref" in block:
            block = lookup(block['$ref'], raw_spec)
        for k, v in block.items():
            if isinstance(v, list):
                if k not in merged:
                    merged[k] = v
                else:
                    merged[k] += v
                    merged[k] = list(set(merged[k]))
            elif isinstance(v, dict):
                if k not in merged:
                    merged[k] = v
                else:
                    merged[k].update(v)
            else:
                merged[k] = v
    return merged


class _spinner(object):

    @staticmethod
    def draw(event):
        if settings.colored_output:
            cursor = itertools.cycle('|/-\\')
            while not event.isSet():
                sys.stdout.write(next(cursor))
                sys.stdout.flush()
                time.sleep(0.1)
                sys.stdout.write('\b')
            sys.stdout.write(' ')
            sys.stdout.flush()

    def __init__(self):
        self.event = threading.Event()
        self.thread = threading.Thread(target=_spinner.draw,
                                       args=(self.event,))
        self.thread.daemon = True

    def __enter__(self):
        self.thread.start()

    def __exit__(self, type, value, traceback):
        self.event.set()
        self.thread.join()
