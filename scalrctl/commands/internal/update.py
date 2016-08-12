# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import threading

import yaml
import requests

from scalrctl import click, defaults, settings, commands

__author__ = 'Dmitriy Korsakov, Sergey Babak'


class _spinner(object):

    @staticmethod
    def cursor():
        while True:
            for cursor in '|/-\\':
                yield cursor

    @staticmethod
    def draw(event):
        spinner = _spinner.cursor()
        while not event.isSet():
            sys.stdout.write(next(spinner))
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write('\b')
        sys.stdout.write(' ')
        sys.stdout.flush()

    def __init__(self):
        self.event = threading.Event()
        self.thread = threading.Thread(target=_spinner.draw,
                                       args=(self.event,))

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


def _write_routes(api_level, paths):
    routes_text = _read_spec(defaults.ROUTES_PATH) or '{}'
    routes = json.loads(routes_text)
    routes[api_level] = paths
    json.dump(routes, open(defaults.ROUTES_PATH, "w"))


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
            paths = list(struct['paths'].keys())
        except (KeyError, TypeError, yaml.YAMLError):
            raise Exception('Swagger specification is not valid')

        yaml_spec_path = _get_spec_path(api_level, 'yaml')
        json_spec_path = _get_spec_path(api_level, 'json')

        old_yaml_spec_text = _read_spec(yaml_spec_path)

        # update yaml spec
        if yaml_spec_text != old_yaml_spec_text:
            _write_spec(yaml_spec_path, yaml_spec_text)

        # update json spec and routes
        _write_spec(json_spec_path, json_spec_text)
        _write_routes(api_level, paths)

        return True, None
    except Exception as e:
        return False, str(e) or 'Unknown reason'


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
                  _is_spec_exists(api, 'json') for api in settings.API_LEVELS]
        exists.append(os.path.exists(defaults.ROUTES_PATH))
        return not all(exists)


def update():
    """
    Update spec for all available APIs.
    """

    amount = len(settings.API_LEVELS)

    for index, api_level in enumerate(settings.API_LEVELS, 1):

        click.echo('[{}/{}] Updating specifications for {} API ... '
                   .format(index, amount, api_level), nl=False)

        with _spinner():
            success, fail_reason = _update_spec(api_level)

        if success:
            click.secho('Done', fg='green')
        else:
            click.secho('Failed: {}'.format(fail_reason), fg='red')
