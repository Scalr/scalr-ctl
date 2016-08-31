"""
Pytest plugins and fixtures.
"""
import json
import os

import pytest

from scalrctl import defaults


def _read_scheme():
    with open(os.path.join(defaults.PROJECT_DIR,
                           'scheme/scheme.json')) as file_:
        return json.load(file_)


@pytest.fixture(scope='module')
def commands(scheme=None, cmds=None):
    """
    Returns all scalr-ctl commands.
    """
    scheme = scheme or _read_scheme()
    cmds = cmds or []
    data = []

    for cmd, values in scheme.items():
        if isinstance(values, dict):
            if 'route' not in values:
                data.extend(commands(scheme=values, cmds=cmds + [cmd]))
            data.append(cmds + [cmd])
    return data
