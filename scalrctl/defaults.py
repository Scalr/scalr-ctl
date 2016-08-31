__author__ = 'Dmitriy Korsakov'

import os

CONFIG_DIRECTORY = os.path.expanduser(os.environ.get("SCALRCLI_HOME", os.path.join(os.path.expanduser("~"), ".scalr")))
CONFIG_PATH = os.path.join(CONFIG_DIRECTORY, "%s.yaml" % os.environ.get("SCALRCLI_PROFILE", "default"))
VERSION = open(os.path.join(os.path.dirname(__file__), "VERSION")).read().strip()
ROUTES_PATH = os.path.join(CONFIG_DIRECTORY, "available_api_routes.json")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

API_LEVELS = [
    'user',
    'account',
    'global',
]