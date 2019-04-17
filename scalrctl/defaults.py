__author__ = 'Dmitriy Korsakov'

import os

CONFIG_DIRECTORY = os.path.expanduser(os.environ.get("SCALRCLI_HOME", os.path.join(os.path.expanduser("~"), ".scalr")))
CONFIG_PATH = os.path.join(CONFIG_DIRECTORY, "%s.yaml" % os.environ.get("SCALRCLI_PROFILE", "default"))
VERSION = open(os.path.join(os.path.dirname(__file__), "VERSION")).read().strip()
OPENAPI_ENABLED = os.path.exists(os.path.join(CONFIG_DIRECTORY, 'openapi.json'))
SCHEME_FNAME = "scheme_openapi.json" if OPENAPI_ENABLED else "scheme.json"
SCHEME_PATH = os.path.join(os.path.dirname(__file__), 'scheme', SCHEME_FNAME)
API_LEVELS = [
    'user',
    'account',
    'global',
]
