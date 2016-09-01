# -*- coding: utf-8 -*-
import os
import re

import yaml

from scalrctl import click, commands, defaults, settings
from scalrctl.commands.internal import bash_complete, update

__author__ = 'Dmitriy Korsakov, Sergey Babak'


CONFIGURATIONS = {
    'USER': {
        'API_SCHEME': {
            'order': 0,
            'description': 'Scalr API scheme',
            'enum': ['http', 'https'],
        },
        'SSL_VERIFY_PEER': {
            'order': 1,
            'dependencies': {
                'API_SCHEME': 'https',
            },
            'description': 'SSL verification',
        },
        'API_HOST': {
            'pattern': r'^(?!http://|https://).*',
            'order': 2,
            'description': 'Scalr API host (without protocol)'
        },
        'API_KEY_ID': {
            'order': 3,
            'description': 'Scalr API key ID'
        },
        'API_SECRET_KEY': {
            'order': 4,
            'description': 'Scalr API sectet key ID'
        },
        'envId': {
            'pattern': r'^\d+$',
            'order': 5,
            'description': 'Scalr environment ID'
        },
        'view': {
            'order': 8,
            'description': 'View mode',
            'enum': ['tree', 'table', 'json']
        },
        'colored_output': {
            'order': 9,
            'description': 'Colored output'
        },
    },
    'ADMIN': {
        'GLOBAL_SCOPE_API_KEY_ID': {
            'order': 6,
            'description': 'Scalr admin (global scope) API key ID'
        },
        'GLOBAL_SCOPE_API_SECRET_KEY': {
            'order': 7,
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
        return "Set configuration options in interactive mode"

    def get_options(self):
        admin_opt = click.Option(('--with-global-scope', 'admin'),
                                 required=False, is_flag=True)
        return [admin_opt, ]


def configure(admin=False):
    """
    Configure command-line client.
    Creates new profile in configuration directory
    and downloads spec files.
    :param admin: configure admin (global scope) values
    """

    conf_path = defaults.CONFIG_PATH

    conf_data = _read_config(conf_path) or {}

    values = CONFIGURATIONS['USER']
    if admin:
        values.update(CONFIGURATIONS['ADMIN'])

    click.echo('Configuring...')

    for key, value in sorted(values.items(), key=lambda kv: kv[1]['order']):

        default_value = getattr(settings, key)

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

            # check spaces
            if type(conf_data.get(key)) == str and ' ' in conf_data.get(key):
                return False

            # check pattern
            if value.get('pattern'):
                pattern = re.compile(value['pattern'])
                if not pattern.match(conf_data[key]):
                    return False

            # check enum
            return conf_data.get(key) in enum if enum else True

        while not _input():
            click.echo('Error: invalid input')

    _write_config(conf_path, conf_data)
    click.echo('\nNew config saved to {}\n'.format(conf_path))

    apply_settings(conf_data)
    update.update()
    bash_complete.setup_bash_complete()


def apply_settings(data):
    for key, value in data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)