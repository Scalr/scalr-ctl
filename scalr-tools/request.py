import time
import hmac
import hashlib
import binascii
import urlparse
import urllib
import urllib2


SIGNATURE_VERSION = 'V1-HMAC-SHA256'
API_KEY_ID = 'APIKBEFGKMORSUVWYZ38'
API_SECRET_KEY = 'CI+to0AZG/b+oSzg6iQpyQGjMKuKdvlto7TmZuWu'
API_SCHEME = 'https'
API_HOST = 'newapi.scalr.net'
API_REQUEST_URI = '/api/user/v1/os/'
API_METHOD = 'GET'
API_DEBUG = 0


def request(method, scheme, api_host, request_uri, query_data=None, debug=False):
    query_string = urllib.urlencode(query_data) if query_data else ''
    time_iso8601 = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

    string_to_sign = "%s\n%s\n%s\n%s\n" % (method.upper(), time_iso8601, request_uri, query_string)
    digest = hmac.new(API_SECRET_KEY, string_to_sign, hashlib.sha256).digest()
    signature = binascii.b2a_base64(digest).strip()

    headers = dict()
    headers['Content-Type'] = 'application/json; charset=utf-8'
    headers['X-Scalr-Key-Id'] = API_KEY_ID
    headers['X-Scalr-Date'] = time_iso8601
    headers['X-Scalr-Signature'] = "%s %s" % (SIGNATURE_VERSION, signature)
    if debug:
        headers['X-Scalr-Debug'] = 1

    url = urlparse.urlunsplit((scheme, api_host, request_uri, query_string, ''))

    print "url: %s" % url
    print "headers: %s" % headers

    req = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(req)
    result = response.read()
    return result


if __name__ == '__main__':
    print request("get", API_SCHEME, API_HOST, API_REQUEST_URI, {'maxResults': 2})