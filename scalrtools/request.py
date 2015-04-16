import sys
import time
import hmac
import hashlib
import binascii
import urlparse
import urllib
import urllib2
import json

import click

from scalrtools import settings


def request(method, request_uri, query_data=None):
    method = method.upper()
    scheme = settings.API_SCHEME
    api_host = settings.API_HOST
    debug = 0 #settings.API_DEBUG
    query_string = urllib.urlencode(query_data) if query_data else ''
    time_iso8601 = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

    try:
        assert settings.API_KEY_ID
        assert settings.API_SECRET_KEY
        
        string_to_sign = "%s\n%s\n%s\n%s\n" % (method.upper(), time_iso8601, request_uri, query_string)
        digest = hmac.new(settings.API_SECRET_KEY, string_to_sign, hashlib.sha256).digest()
        signature = binascii.b2a_base64(digest).strip()

        headers = dict()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        headers['X-Scalr-Key-Id'] = settings.API_KEY_ID
        headers['X-Scalr-Date'] = time_iso8601
        headers['X-Scalr-Signature'] = "%s %s" % (settings.SIGNATURE_VERSION, signature)
        if debug:
            headers['X-Scalr-Debug'] = 1

        url = urlparse.urlunsplit((scheme, api_host, request_uri, query_string, ''))

        if settings.debug_mode:
            click.echo("%s URL: %s" % (method, url))
            click.echo("Headers: %s " % json.dumps(headers, indent=2))


        req = urllib2.Request(url, headers=headers)
        req.get_method = lambda: method
        response = urllib2.urlopen(req)
        result = response.read()
    except BaseException, e:
        if settings.debug_mode:
            raise
        raise click.ClickException(str(e))
    return result
