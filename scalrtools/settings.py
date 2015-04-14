__author__ = 'shaitanich'

import os
import yaml


API_KEY_ID = None

API_SECRET_KEY = None

envId = None

view = "tree"

debug_mode = False

API_SCHEME = 'https'

API_HOST = 'my.scalr.net'

SIGNATURE_VERSION = 'V1-HMAC-SHA256'

spec = yaml.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "swagger.yaml"), "r"))
