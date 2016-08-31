"""
Tests for --help option.
"""
import os

from scalrctl.click.testing import CliRunner
from scalrctl.app import cli


STUBS_DIR = os.path.join(os.path.dirname(__file__), 'stubs')


def _mkdir_recursive(path):
    sub_path = os.path.dirname(path)
    if not os.path.exists(sub_path):
        _mkdir_recursive(sub_path)
    if not os.path.exists(path):
        os.mkdir(path)


def save_help(commands):
    """
    Saves --help output for all scalr-ctl commands.
    """
    if os.path.exists(STUBS_DIR):
        for file_ in os.listdir(STUBS_DIR):
            os.remove(os.path.join(STUBS_DIR, file_))
    else:
        _mkdir_recursive(STUBS_DIR)

    runner = CliRunner()

    for command in commands:
        result = runner.invoke(cli, command + ['--help'])
        file_name = os.path.join(STUBS_DIR, '>'.join(command))
        with open(file_name, 'w') as file_:
            file_.write(result.output)


def test_help(commands):
    """
    Regression test for --help option.
    """
    assert os.path.exists(STUBS_DIR), "Stubs directory does not exist"

    names = ['>'.join(command) for command in commands]
    files = os.listdir(STUBS_DIR)

    for file_ in files:
        assert file_ in names, ("Command {} is missing"
                                .format(file_.replace('>', ' ')))

    for name in names:
        assert name in files, ("Unexpected command {}"
                               .format(name))

    runner = CliRunner()
    for command in commands:
        result = runner.invoke(cli, command + ['--help'])
        file_name = os.path.join(STUBS_DIR, '>'.join(command))
        with open(file_name, 'r') as file_:
            assert result.output == file_.read(), ("Found changes in --help "
                                                   "for 'scalr-ctl {}'"
                                                   .format(' '.join(command)))
