__author__ = 'Dmitriy Korsakov'

import os

CONFIG_FOLDER = os.path.expanduser(os.environ.get("SCALRCLI_HOME", os.path.join(os.path.expanduser("~"), ".scalr")))
CONFIG_PATH = os.path.join(CONFIG_FOLDER, "%s.yaml" % os.environ.get("SCALRCLI_PROFILE", "default"))
