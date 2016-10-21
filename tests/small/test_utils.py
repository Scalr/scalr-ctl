# -*- coding: utf-8 -*-
import os

from scalrctl import defaults, settings, utils


def test_read_spec():
    for api_level in defaults.API_LEVELS:
        base_path = '/api/{}/{}'.format(settings.API_VERSION, api_level)
        for ext in ('yaml', 'json'):
            spec = utils.read_spec(api_level, ext=ext)
            assert spec.get('paths')
            assert spec.get('definitions')
            assert spec.get('basePath') == base_path


def test_read_routes():
    routes = utils.read_routes()
    for api_level in defaults.API_LEVELS:
        spec = utils.read_spec(api_level, ext='json')
        assert api_level in routes
        assert len(routes[api_level]) == len(spec['paths'])


def test_read_scheme(scheme=None):
    scheme = scheme or utils.read_scheme()
    for command, data in scheme.items():
        if type(data) == dict:
            if data.get('route'):
                assert data.get('class')
                assert data.get('http-method')
                assert data.get('api_level')
            else:
                test_read_scheme(scheme=data)


def test_read_config():
    if os.path.exists(defaults.CONFIG_DIRECTORY):
        config = utils.read_config()
        assert config

        config = utils.read_config(profile='qwerty')
        assert not config
