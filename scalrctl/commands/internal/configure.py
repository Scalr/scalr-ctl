# -*- coding: utf-8 -*-
import os

import yaml
import json
import posixpath

from six.moves.urllib import parse

from scalrctl import click, commands, defaults, settings, request
from scalrctl.commands.internal import bash_complete, update

__author__ = 'Dmitriy Korsakov, Sergey Babak'


CONFIGURATIONS = {
    'USER': {
        'API_HOST': {
            'order': 0,
            'description': 'Scalr API host'
        },
        'API_SCHEME': {
            'order': 1,
            'description': 'Scalr API scheme',
            'enum': ['http', 'https'],
        },
        'SSL_VERIFY_PEER': {
            'order': 2,
            'dependencies': {
                'API_SCHEME': 'https',
            },
            'description': 'SSL verification',
        },
        'API_KEY_ID': {
            'order': 3,
            'description': 'Scalr API key ID'
        },
        'API_SECRET_KEY': {
            'order': 4,
            'description': 'Scalr API secret key ID'
        },
        'envId': {
            'order': 5,
            'description': 'Scalr environment ID'
        },
        'accountId': {
            'order': 6,
            'description': 'Scalr account ID',
        },
        'view': {
            'order': 9,
            'description': 'View mode',
            'enum': ['tree', 'table', 'json']
        },
        'colored_output': {
            'order': 10,
            'description': 'Colored output'
        },
    },
    'ADMIN': {
        'GLOBAL_SCOPE_API_KEY_ID': {
            'order': 7,
            'description': 'Scalr admin (global scope) API key ID'
        },
        'GLOBAL_SCOPE_API_SECRET_KEY': {
            'order': 8,
            'description': 'Scalr admin (global scope) API secret key'
        },
    }
}


def _read_config(conf_path):
    if os.path.exists(conf_path):
        return yaml.load(open(conf_path, 'r'))


def _write_config(conf_path, conf_data):

    if not os.path.exists(defaults.CONFIG_DIRECTORY):
        os.makedirs(defaults.CONFIG_DIRECTORY)

    raw_data = yaml.dump(conf_data, default_flow_style=False, default_style='')
    with open(conf_path, 'w') as fp:
        fp.write(raw_data)


class ConfigureScalrCTL(commands.BaseAction):

    def run(self, *args, **kwargs):
        configure(**kwargs)

    def get_description(self):
        return "Set user configuration options in interactive mode"

    def get_options(self):
        profile_arg = click.Argument(('profile',), required=False)   # [ST-30]
        hlp = 'Add API credentials for Global scope'
        admin_opt = click.Option(('--with-global-scope', 'admin'), required=False, is_flag=True, help=hlp)
        return [profile_arg, admin_opt]


def configure(profile=None, admin=False):
    """
    Configure command-line client.
    Creates new profile in configuration directory
    and downloads spec files.
    :param profile: profile name
    :param admin: configure admin(global scope) values
    """

    conf_path = defaults.CONFIG_PATH if not profile else \
        os.path.join(defaults.CONFIG_DIRECTORY, '{}.yaml'.format(profile))

    conf_data = _read_config(conf_path) or {}

    values = CONFIGURATIONS['USER']
    if admin:
        values.update(CONFIGURATIONS['ADMIN'])

    click.echo('Configuring profile "{}":\n'.format(profile or 'default'))

    for key, value in sorted(values.items(), key=lambda kv: kv[1]['order']):

        default_value = getattr(settings, key)

        if key == "accountId" and not default_value:
            default_value = get_default_account_id(get_session_data(conf_data))

        desc = value.get('description') or key
        deps = value.get('dependencies')
        enum = value.get('enum')

        if deps and not all(conf_data[k] == v for k, v in deps.items()):
            continue

        if enum:
            desc = '{}. Choose from {}'.format(desc, ', '.join(enum))

        def _input():
            if type(default_value) in (bool,):
                conf_data[key] = click.confirm(desc, default=default_value)
            elif type(default_value) in (int, str) or default_value is None:
                conf_data[key] = click.prompt(desc, default=default_value)
                conf_data[key] = str(conf_data[key]).strip()

            return conf_data.get(key) in enum if enum else True

        while not _input():
            continue

        if key == "API_HOST":
            split_result = parse.urlsplit(conf_data[key])
            supported_schemas = values['API_SCHEME']['enum']
            if split_result.scheme and split_result.scheme in supported_schemas:
                url = split_result.netloc
                if split_result.path:
                    url_path = split_result.path[1:] if split_result.path.startswith('/') else split_result.path
                    url = posixpath.join(url, url_path)
                conf_data['API_HOST'] = url
                setattr(settings, 'API_SCHEME', split_result.scheme)

    _write_config(conf_path, conf_data)
    click.echo('\nNew config saved to {}\n'.format(conf_path))

    apply_settings(conf_data)
    update.update()
    bash_complete.setup_bash_complete()


def apply_settings(data):
    for key, value in data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)


def get_session_data(data):
    try:
        api_level = (data['API_KEY_ID'], data['API_SECRET_KEY'])
        uri = '/api/%s/session/' % data['API_VERSION']
        raw_result = request.request(method="get", api_level=api_level, request_uri=uri)
        result = json.loads(raw_result)
    except:
        result = {}
    return result


def get_default_account_id(session_data):
    try:
        account_id = session_data["data"]['environments'][0]['accountId']
    except KeyError:
        account_id = None
    return account_id
