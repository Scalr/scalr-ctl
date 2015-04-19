import sys
import time
import hmac
import hashlib
import binascii
import urlparse
import urllib
import json
import yaml

import click
import requests

from scalrtools import settings

try:
    requests.packages.urllib3.disable_warnings()
except:
    pass

def request(method, request_uri, payload=None, data=None):
    scheme = settings.API_SCHEME
    api_host = settings.API_HOST
    time_iso8601 = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    try:
        query_string = urllib.urlencode(sorted(payload.items())) if payload else ''
        body = json.dumps(yaml.safe_load(data)) if data else '' #XXX

        assert settings.API_KEY_ID, "No Key ID"
        assert settings.API_SECRET_KEY, "No Secret key"

        string_to_sign = "%s\n%s\n%s\n%s\n%s" % (method.upper(), time_iso8601, request_uri, query_string, body)
        #string_to_sign = "%s\n%s\n%s\n%s\n%s" % ("GET", time_iso8601, request_uri, query_string, "")
        if settings.debug_mode:
            #DELETE: needed to debug "requests" module on OSX (works fine on linux)
            print "stringToSign:"
            print string_to_sign
        digest = hmac.new(settings.API_SECRET_KEY, string_to_sign, hashlib.sha256).digest()
        signature = binascii.b2a_base64(digest).strip()

        headers = dict()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        headers['X-Scalr-Key-Id'] = settings.API_KEY_ID
        headers['X-Scalr-Date'] = time_iso8601
        headers['X-Scalr-Signature'] = "%s %s" % (settings.SIGNATURE_VERSION, signature)
        #if hasattr(settings, "API_DEBUG") and settings.API_DEBUG:
        headers['X-Scalr-Debug'] = 1

        url = urlparse.urlunsplit((scheme, api_host, request_uri, '', ''))

        if settings.debug_mode:
            click.echo("%s URL: %s" % (method.upper(), url))
            click.echo("Headers: %s " % json.dumps(headers, indent=2))

        r = requests.request(method.lower(), url, data=body, params=payload, headers=headers)
        result = r.text


    except (Exception, BaseException), e:
        if settings.debug_mode:
            raise
        raise click.ClickException(str(e))
    return result
