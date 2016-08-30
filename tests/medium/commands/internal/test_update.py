# -*- coding: utf-8 -*-
import os

import pytest
import webob
from wsgi_intercept import add_wsgi_intercept, remove_wsgi_intercept,\
    requests_intercept

from scalrctl import defaults, settings
from scalrctl.app import cli
from scalrctl.click.testing import CliRunner
from scalrctl.commands.internal import update


class HTTPMockServer(object):

    def __init__(self, status=200, validity=True, host='localhost', port=80):
        self.status = status
        self.validity = validity
        self.host = host
        self.port = port

        self._api_host = settings.API_HOST
        self._api_scheme = settings.API_SCHEME
        self._routes = HTTPMockServer._routes()

    @staticmethod
    def _routes():
        data = {}

        # routes for internal commands
        for api_level in defaults.API_LEVELS:
            route = '/api/{}.{}.yml'.format(api_level, settings.API_VERSION)
            if route not in data:
                data[route] = {}
            data[route][200] = update._load_yaml_spec(api_level)

        return data

    def _app(self, environ, start_response):
        if self.validity:
            data = self._routes.get(environ['PATH_INFO'])
            body = data.get(self.status, '') if data else ''
        else:
            body = "not valid"
        resp = webob.Response(status=self.status, body=body)
        return resp(environ, start_response)

    def setup(self):
        settings.API_HOST = '{}:{}'.format(self.host, self.port)
        settings.API_SCHEME = 'http'
        requests_intercept.install()
        add_wsgi_intercept(self.host, self.port, lambda: self._app)

    def teardown(self):
        settings.API_HOST = self._api_host
        settings.API_SCHEME = self._api_scheme
        requests_intercept.uninstall()
        remove_wsgi_intercept(self.host, self.port)


@pytest.fixture(scope='function')
def server():
    mock_server = HTTPMockServer()
    mock_server.setup()
    yield mock_server
    mock_server.teardown()


def test_update(server):
    runner = CliRunner()
    api_len = len(defaults.API_LEVELS)

    with runner.isolated_filesystem() as tmp_folder:
        config_dir = defaults.CONFIG_DIRECTORY
        defaults.CONFIG_DIRECTORY = tmp_folder

        def call_update():
            result = runner.invoke(cli, ['update'])
            assert result.exit_code == 0
            return result.output

        def remove_configs(ext):
            for f in os.listdir(defaults.CONFIG_DIRECTORY):
                if os.path.isfile(f) and f.endswith('.{}'.format(ext)):
                    os.remove(f)

        try:
            # empty config directory
            assert update.is_update_required()
            expected_msg = "Done"
            assert call_update().count(expected_msg) == api_len
            assert not update.is_update_required()

            # json copies does not exists
            remove_configs('json')
            assert update.is_update_required()
            assert call_update().count(expected_msg) == api_len
            assert not update.is_update_required()

            # yaml response not valid
            server.validity = False
            expected_msg = "Failed: Swagger specification is not valid"
            assert call_update().count(expected_msg) == api_len

            # 404 status code
            server.validity = True
            server.status = 404
            expected_msg = "Failed: Can't load spec file"
            assert call_update().count(expected_msg) == api_len

            # config directory does not exists
            server.status = 200
            defaults.CONFIG_DIRECTORY = '/tmp/i7Lzcdm5uOcfqVkDTKRQ/'
            expected_msg = "Failed: [Errno 2] No such file or directory"
            assert call_update().count(expected_msg) == api_len
        finally:
            defaults.CONFIG_DIRECTORY = config_dir
