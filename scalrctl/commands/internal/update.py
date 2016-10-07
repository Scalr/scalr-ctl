# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import itertools
import threading
import traceback

import six
import yaml
import requests

from scalrctl import click, defaults, settings, commands

__author__ = 'Dmitriy Korsakov, Sergey Babak'


class _spinner(object):

    @staticmethod
    def draw(event):
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
    resp = requests.get(spec_url, verify=settings.SSL_VERIFY_PEER)
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

        with _spinner():
            success, fail_reason = _update_spec(api_level)

        if success:
            click.secho('Done', fg='green')
        else:
            click.secho('Failed: {}'.format(fail_reason), fg='red')

