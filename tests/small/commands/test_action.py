# -*- coding: utf-8 -*-
import pydoc

import pytest

from scalrctl import settings, defaults, utils


@pytest.fixture(scope='module')
def specs():
    data = {}
    for api_level in defaults.API_LEVELS:
        data[api_level] = utils.read_spec(api_level, ext='json')
    return data


@pytest.fixture(scope='module')
def actions():
    scheme = utils.read_scheme()

    def _parse(cmd_dict, objects=[]):
        for command, data in cmd_dict.items():
            if type(data) == dict:
                if data.get('route'):
                    cls = pydoc.locate(data['class'])
                    action = cls(name=command,
                                 route=data['route'],
                                 http_method=data['http-method'],
                                 api_level=data['api_level'])
                    action.validate()
                    objects.append(action)
                else:
                    _parse(data, objects=objects)
        return objects

    return _parse(scheme)


def test_run():
    pass


def test_get_description(actions, specs):
    for action in actions:
        dc = specs[action.api_level]['paths'][action.route][action.http_method]
        assert action.get_description() == dc['description']


def test_modify_options(actions):
    for action in actions:
        settings.envId = 1
        for option in action.modify_options(action.get_options()):
            if option.name == 'envId':
                assert not option.required

            if action.prompt_for and option.name in action.prompt_for:
                assert option.prompt == option.name


def test_get_options(actions, specs):
    for action in actions:
        route_data = specs[action.api_level]['paths'][action.route]
        params = len(route_data.get('parameters', ''))
        if action.http_method.lower() in ('get', 'delete'):
            params += len(route_data[action.http_method].get('parameters', ''))

        assert params == len(action._get_default_options())


def test_validate():
    pass
