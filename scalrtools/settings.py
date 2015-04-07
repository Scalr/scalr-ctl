__author__ = 'shaitanich'

import os
import yaml

API_KEY_ID = 'APIKBEFGKMORSUVWYZ38'

API_SECRET_KEY = 'CI+to0AZG/b+oSzg6iQpyQGjMKuKdvlto7TmZuWu'

envId = "3414"

view = "tree"

debug_mode = False

API_SCHEME = 'https'

API_HOST = 'my.scalr.net'

API_DEBUG = 0

SIGNATURE_VERSION = 'V1-HMAC-SHA256'

spec_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "swagger.yaml")

spec = yaml.load(open(spec_path, "r"))
