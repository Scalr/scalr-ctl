__author__ = 'Dmitriy Korsakov'

import os
import time
import hmac
import hashlib
import binascii
import urlparse
import urllib
import json
import yaml

import requests

CONFIG_FOLDER = os.path.expanduser(os.environ.get("SCALRCLI_HOME", "~/.scalr"))
SWAGGER_USER_FILE = "user.yaml"
SWAGGER_USER_PATH = os.path.join(CONFIG_FOLDER, SWAGGER_USER_FILE)
SWAGGER_USER_JSONSPEC_FILE = SWAGGER_USER_FILE.split(".")[0] + ".json"
SWAGGER_USER_JSONSPEC_PATH = os.path.join(CONFIG_FOLDER, SWAGGER_USER_JSONSPEC_FILE)


class BaseConnection(object):

    def __init__(self, api_host, api_scheme, api_key_id, api_secret_key, api_version, signature_version, env_id):
        self.api_host = api_host
        self.api_scheme = api_scheme
        self.api_key_id = api_key_id
        self.api_secret_key = api_secret_key
        self.api_version = api_version
        self.signature_version = signature_version
        self.env_id = env_id


    def _get_signature(self, method, request_uri, payload, body, time_iso8601):
        query_string = urllib.urlencode(sorted(payload.items())) if payload else ''
        string_to_sign = "%s\n%s\n%s\n%s\n%s" % (method.upper(), time_iso8601, request_uri, query_string, body)
        digest = hmac.new(self.api_secret_key, string_to_sign, hashlib.sha256).digest()
        return binascii.b2a_base64(digest).strip()


    def request(self, method, request_uri, payload=None, data=None):
        body = json.dumps(yaml.safe_load(data)) if data else '' #XXX
        time_iso8601 = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        signature = self._get_signature(method, request_uri, payload, body, time_iso8601)

        headers = dict()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        headers['X-Scalr-Key-Id'] =  self.api_key_id
        headers['X-Scalr-Date'] = time_iso8601
        headers['X-Scalr-Signature'] = "%s %s" % (self.signature_version, signature)

        url = urlparse.urlunsplit((self.api_scheme, self.api_host, request_uri, '', ''))
        r = requests.request(method.lower(), url, data=body, params=payload, headers=headers)
        return json.loads(r.text)


class Connection(BaseConnection):

    _spec = None

    def __init__(self, api_host, api_scheme, api_key_id, api_secret_key, api_version, signature_version, env_id):
        super(Connection, self).__init__(
            api_host, api_scheme, api_key_id, api_secret_key, api_version, signature_version, env_id
        )
        self._spec = self._get_spec()


    def _get_spec_url(self, api_level="user"):
        return "{0}://{1}/api/{2}.{3}.yml".format(self.api_scheme, self.api_host, api_level, self.api_version)


    def _get_spec(self):
        """
        Downloads yaml spec and converts it to JSON
        JSON file is stored in configuration directory.
        """
        if self._spec:
            return

        if os.path.exists(SWAGGER_USER_JSONSPEC_PATH):
            struct = json.load(open(SWAGGER_USER_JSONSPEC_PATH))
        else:
            r = requests.get(self._get_spec_url())
            struct = yaml.load(r.text)
            json.dump(struct, open(SWAGGER_USER_JSONSPEC_PATH, "w"))

        return struct


    def list_methods(self):
        """
        #TODO: automatically download spec
        """
        l = []
        for route in self._spec["paths"]:
            for method in self._spec["paths"][route].keys():
                if method != "parameters":
                    l.append((str(route), str(method)))
        return l


    def _get_route_alias(self, route):
        parts = route.split('/')

        if len(parts) < 2:
            return

        alias = ''

        for part in parts:
            if part and not part.startswith('{'):
                alias += "_%s" % part.replace("-", "_")

        return alias[1:]


if __name__ == "__main__":

    import settings

    conn = Connection(
        api_host=settings.API_HOST,
        api_scheme=settings.API_SCHEME,
        api_key_id=settings.API_KEY_ID or os.environ.get("SCALR_API_KEY_ID"),
        api_secret_key=settings.API_SECRET_KEY or os.environ.get("SCALR_API_SECRET_KEY"),
        api_version=settings.API_VERSION,
        signature_version=settings.SIGNATURE_VERSION,
        env_id=settings.envId
    )

    #print conn.request("get", "/api/user/v1beta0/os/")
    for m in conn.list_methods():
        print m