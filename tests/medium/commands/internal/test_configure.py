# -*- coding: utf-8 -*-
import io
import os
import random

from scalrctl import defaults, settings
from scalrctl.app import cli
from scalrctl.click.testing import CliRunner
from scalrctl.commands.internal import configure


VALID_API_HOST = settings.API_HOST


def _valid_input(key, value, default_type):
    if isinstance(value.get('enum'), list):
        return random.choice(value['enum'])
    elif default_type == bool:
        return random.choice(('y', 'n'))
    elif value.get('pattern') == r'^\d+$':
        return random.randint(0, 1000)
    else:
        return VALID_API_HOST if key == 'API_HOST' else 'test'


def _invalid_input(key):
    if key == 'API_HOST':
        return '{}://test'.format(random.choice(('http', 'https')))
    else:
        return ' '.join(random.choice('abcde') for _ in range(10))


def _random_input_genertor(admin=False, invalid_values_quantity=3):
    """
    Generates a sequence of input values with valid and invalid data.
    """
    input_data = []
    valid_data = {}

    values = configure.CONFIGURATIONS['USER']
    if admin:
        values.update(configure.CONFIGURATIONS['ADMIN'])

    for key, value in sorted(values.items(), key=lambda kv: kv[1]['order']):
        default_type = type(getattr(settings, key))
        deps = value.get('dependencies')
        if deps and not all(valid_data[k] == v for k, v in deps.items()):
            continue

        for item in range(0, invalid_values_quantity):
            invalid_input = _invalid_input(key)
            input_data.append(invalid_input)

        valid_input = _valid_input(key, value, default_type)
        input_data.append(valid_input)

        if default_type == bool:
            valid_data[key] = True if valid_input.lower() == 'y' else False
        else:
            valid_data[key] = str(valid_input)

    input_data = [str(item) for item in input_data]
    input_data = io.BytesIO('\n'.join(input_data).encode('utf-8'))

    return input_data, valid_data


def test_configure():
    """
    Test for "scalr-ctl configure" command.
    """
    runner = CliRunner()

    with runner.isolated_filesystem() as tmp_folder:
        config_path = defaults.CONFIG_PATH
        defaults.CONFIG_PATH = os.path.join(tmp_folder, 'default.yaml')
        try:
            # test "configure" command
            input_data, valid_data = _random_input_genertor()
            result = runner.invoke(cli, ['configure'], input=input_data)
            assert result.exit_code == 0

            config_data = configure._read_config(defaults.CONFIG_PATH)
            assert len(set(config_data.items()) ^
                       set(valid_data.items())) == 0

            # test "--with-global-scope" option
            os.remove(defaults.CONFIG_PATH)
            input_data, valid_data = _random_input_genertor(admin=True)
            result = runner.invoke(cli, ['configure', '--with-global-scope'],
                                   input=input_data)
            assert result.exit_code == 0

            config_data = configure._read_config(defaults.CONFIG_PATH)
            assert len(set(config_data.items()) ^
                       set(valid_data.items())) == 0
        finally:
            defaults.CONFIG_PATH = config_path
