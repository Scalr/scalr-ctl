# -*- coding: utf-8 -*-
import os

import six
import pytest
from pretenders.client.http import HTTPMock
from pretenders.common.constants import FOREVER

from scalrctl import defaults, settings
from scalrctl.app import cli
from scalrctl.click.testing import CliRunner
from scalrctl.commands.internal import update


class HTTPMockServer(HTTPMock):

    def __init__(self, status=200, validity=True):
        self._api_host = settings.API_HOST
        self._api_scheme = settings.API_SCHEME

        self.__status = status
        self.__validity = validity

        self._routes = HTTPMockServer._routes()
        super(HTTPMock, self).__init__('localhost', 8000, name='test')

    def setup(self):
        self.teardown()
        self._setup_routes()
        settings.API_HOST = self.pretend_url.replace('http://', '')
        settings.API_SCHEME = 'http'

    def teardown(self):
        settings.API_HOST = self._api_host
        settings.API_SCHEME = self._api_scheme

    def _setup_routes(self):
        self.reset()
        for route, data in self._routes:
            text = data.get(self.status, '') if self.validity else "not valid"
            if six.PY3:
                text = bytes(text, encoding='utf-8')
            self.when(route).reply(text, status=self.status, times=FOREVER)

    @staticmethod
    def _routes():
        data = {}

        # routes for internal commands
        for api_level in defaults.API_LEVELS:
            path = "/api/{}.{}.yml".format(api_level, settings.API_VERSION)
            route = "GET {}".format(path)
            if route not in data:
                data[route] = {}
            data[route][200] = update._load_yaml_spec(api_level)
        return data.items()

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, value):
        if value not in (200, 201, 204, 400, 401, 403,
                         404, 409, 422, 500, 501, 503):
            raise TypeError('Invalid status')
        self.__status = value
        self.setup()

    @property
    def validity(self):
        return self.__validity

    @validity.setter
    def validity(self, value):
        self.__validity = value
        self.setup()


@pytest.fixture(scope="function")
def server():
    mock_server = HTTPMockServer(status=200, validity=True)
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
