__author__ = 'shaitanich'

import os
import yaml


API_KEY_ID = None

API_SECRET_KEY = None

envId = None

view = "tree"

debug_mode = False

colored_output = True

API_SCHEME = 'https'

API_HOST = 'my.scalr.net'

SIGNATURE_VERSION = 'V1-HMAC-SHA256'

spec_url = "http://repo.scalr.net/swagger.yaml"

spec = yaml.load(open(os.path.join(os.path.expanduser(os.environ.get("SCALR_APICLIENT_CONFDIR", "~/.scalr")), "swagger.yaml"), "r"))
