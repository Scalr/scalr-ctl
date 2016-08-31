"""
Fabric tasks.
"""
from fabric.api import env, execute, local, task, warn_only

from tests.medium import conftest as fixtures
from tests.medium.commands import test_help

env.hosts = ['localhost']
PY_VERSIONS = ('2.7', '3.5')


@task()
def save_help():
    """
    Save --help output for all scalr-ctl commands.
    """
    commands = fixtures.commands()
    test_help.save_help(commands)


@task
def tests():
    """
    Run all tests.
    """
    with warn_only():
        execute(small)
        execute(medium)

@task
def small():
    """
    Run small tests.
    """
    for version in PY_VERSIONS:
        local('python{} -m pytest tests/small/'.format(version))


@task
def medium():
    """
    Run medium tests.
    """
    for version in PY_VERSIONS:
        local('python{} -m pytest -s tests/medium/'.format(version))
