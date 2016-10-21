# -*- coding: utf-8 -*-
import functools
import io
import json
import os
import pydoc
import random
import sys
import tempfile

import pytest

from scalrctl import click, defaults, settings, utils

settings.debug_mode = True
settings.API_KEY_ID = '1'
settings.API_SECRET_KEY = '1'
settings.envId = '1'


@pytest.fixture(scope='module')
def specs():
    return {a: utils.read_spec(a, ext='json') for a in defaults.API_LEVELS}


@pytest.fixture(scope='function')
def actions():
    scheme = utils.read_scheme()
    stdin_text = u'{}'

    def wrapped_edit(f):

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            old_edit = click.edit
            click.edit = lambda x: stdin_text
            value = f(*args, **kwargs)
            click.edit = old_edit
            return value
        return wrapper

    def wrapped_read(f):

        @staticmethod
        @functools.wraps(f)
        def wrapper():
            old_stdin = sys.stdin
            sys.stdin = io.StringIO(stdin_text)
            value = f()
            sys.stdin = old_stdin
            return value
        return wrapper

    def parse_scheme(cmd_dict, objects=[]):
        for command, data in cmd_dict.items():
            if type(data) == dict:
                if data.get('route'):
                    cls = pydoc.locate(data['class'])
                    cls._edit_object = wrapped_edit(cls._edit_object)
                    cls._read_object = wrapped_read(cls._read_object)
                    cls.dry_run = True

                    action = cls(name=command,
                                 route=data['route'],
                                 http_method=data['http-method'],
                                 api_level=data['api_level'])
                    yield action
                else:
                    for item in parse_scheme(data, objects=objects):
                        yield item

    return parse_scheme(scheme)


def test_run():
    for action in actions():
        kwargs = {p['name']: 1 for p in action._get_raw_params()}

        if action.name == 'execute':
            kwargs['nowait'] = True
            kwargs['serverId'] = 1

        for key in kwargs:
            if key in ('eventId', 'cloudCredentialsId'):
                kwargs[key] = '11111111'
            elif key.endswith('Id') and key != 'envId':
                kwargs[key] = '11111111-1111-1111-1111-111111111111'

        assert action.run(**kwargs)


def test_get_description(actions, specs):
    for action in actions:
        dc = specs[action.api_level]['paths'][action.route][action.http_method]
        assert action.get_description() == dc['description']


def test_modify_options(actions):
    for action in actions:
        for option in action.modify_options(action.get_options()):
            if option.name == 'envId':
                assert option.required != bool(settings.envId)

            if action.prompt_for and option.name in action.prompt_for:
                assert option.prompt == option.name


def test_get_options(actions, specs):
    for action in actions:
        route_data = specs[action.api_level]['paths'][action.route]
        params = len(route_data.get('parameters', ''))
        if action.http_method.upper() in ('GET', 'DELETE'):
            params += len(route_data[action.http_method].get('parameters', ''))

        assert params == len(action._get_default_options())


def test_validate(actions):
    api_routes = utils.read_routes()

    temp_dir = tempfile.gettempdir()
    defaults.ROUTES_PATH = os.path.join(temp_dir, '_tmp_scalr_api_routes.json')
    with open(defaults.ROUTES_PATH, 'w') as fp:
        api_routes.pop(random.choice(defaults.API_LEVELS))
        fp.write(json.dumps(api_routes))

    for action in actions:
        is_valid = action.route in api_routes.get(action.api_level, '')
        try:
            action.validate()
        except AssertionError:
            assert not is_valid
        else:
            assert is_valid
