"""
Module that provides utils for client.
"""
# -*- coding: utf-8 -*-
import itertools
import os
import sys
import json
import time
import threading
import traceback
import yaml

from scalrctl import click, defaults, settings


def read_spec(api_level, ext='json'):
    """
    Reads Scalr specification file, json or yaml.
    """

    spec_path = os.path.join(defaults.CONFIG_DIRECTORY,
                             '{}.{}'.format(api_level, ext))

    # pylint: disable=no-else-return
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

    # pylint: disable=no-else-return
    if os.path.exists(spec_path):
        with open(spec_path, 'r') as fp:
            spec_data = fp.read()

        return json.loads(spec_data)
    else:
        msg = "Scalr specification file '{}' does  not exist, " \
              "try to run 'scalr-ctl update'.".format(spec_path)
        raise click.ClickException(msg)


def read_routes():
    """
    Reads routes if exist
    """
    if os.path.exists(defaults.ROUTES_PATH):  # pylint: disable=no-member
        with open(defaults.ROUTES_PATH, 'r') as fp:  # pylint: disable=no-member
            api_routes = fp.read()
        return json.loads(api_routes)


def read_scheme():
    """
    Reads schema
    """
    with open(defaults.SCHEME_PATH) as fp:
        return json.load(fp)


def read_config(profile=None):
    """
    Reads config
    """
    confpath = os.path.join(
        defaults.CONFIG_DIRECTORY,
        '{}.yaml'.format(profile)
    ) if profile else defaults.CONFIG_PATH

    if os.path.exists(confpath):
        with open(confpath, 'r') as fp:
            return yaml.safe_load(fp)


def warning(*messages):
    """
    Prints the warning message(s) to stderr.

    :param tuple messages: The list of the warning messages.
    :rtype: None
    """
    color = 'yellow' if settings.colored_output else None
    for index, message in enumerate(messages or [], start=1):
        index = index if len(messages) > 1 else None
        code = message.get('code') or ''
        text = message.get('message') or ''
        click.secho("Warning{index}{code} {text}".format(
            index=' {}:'.format(index) if index else ':',
            code=' {}:'.format(code) if code else '',
            text=text
        ), err=True, fg=color)


def debug(msg):
    """
    Debug mode
    """
    if settings.debug_mode:
        click.secho("DEBUG: {}".format(msg),
                    fg='green' if settings.colored_output else None)


def reraise(message):
    """
    Reraise error message
    """
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
    """
    Method for detect openapi3
    """
    # pylint: disable=no-else-return
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


def merge_allof(data, raw_spec):
    """
    Merge objects into one from allOf.
    """
    merged = {}
    for block in data:
        if "$ref" in block:
            block = lookup(block['$ref'], raw_spec)
        merge(block, merged)
    return merged


def merge(block, merged):
    """
    Merge values in block.
    """
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


def merge_anyof(data, raw_spec, object_name):
    """
    Merge objects into one from anyOf.
    """
    merged = {}
    data = [a for a in data if a['$ref'].endswith(object_name)]
    for block in data:
        if "$ref" in block:
            block = lookup(block['$ref'], raw_spec)
            if 'allOf' in block:
                for value in block['allOf']:
                    merge(value, merged)
        else:
            merge(block, merged)
    return merged


def merge_all(data, raw_spec, object_name=None):
    """
    Returns merged data from allOf block
    """
    if "allOf" in data:
        merged = merge_allof(data['allOf'], raw_spec)
    elif "anyOf" in data:
        merged = merge_anyof(data['anyOf'], raw_spec, object_name)
    else:
        merged = data

    return merged


class _spinner(object):  # pylint: disable=useless-object-inheritance
    """
    Spinner
    """

    @staticmethod
    def draw(event):
        """
        Draw in console
        """
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

    def __exit__(self, _type, value, _traceback):
        self.event.set()
        self.thread.join()
