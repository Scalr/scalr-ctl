# -*- coding: utf-8 -*-
import binascii
import hashlib
import hmac
import json
import time

import requests
import yaml
from six.moves.urllib.parse import quote, urlunsplit

from scalrctl import click, settings
from scalrctl.compat import urlencode

__author__ = 'Dmitriy Korsakov, Sergey Babak'


"""
import logging

# these two lines enable debugging at httplib level
# (requests->urllib3->httplib) you will see the REQUEST, including
# HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# the only thing missing will be the response.body which is not logged.

import httplib
httplib.HTTPConnection.debuglevel = 1

logging.basicConfig() # you need to initialize logging,
                      # otherwise you will not see anything from requests
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
"""


try:
    requests.packages.urllib3.disable_warnings()
except:
    pass


def _key_pair(api_level='user'):
    """
    Returns key pair(key id and secret key) for specified API scope.
    """

    if api_level in ('global', ):
        api_key_id = settings.GLOBAL_SCOPE_API_KEY_ID
        secret_key = settings.GLOBAL_SCOPE_API_SECRET_KEY
        no_key_msg = "API {} for global scope is not configured. " \
            "Please run 'scalr-ctl configure --admin' to change default " \
            "authentication settings."
        assert api_key_id, no_key_msg.format("Key ID")
        assert secret_key, no_key_msg.format("Secret Key")
    elif api_level in ('user', 'account'):
        api_key_id = settings.API_KEY_ID
        secret_key = settings.API_SECRET_KEY
        no_key_msg = "API {} is not configured. Please specify option " \
            "{} or run 'scalr-ctl configure' to change default " \
            "authentication settings."
        assert api_key_id, no_key_msg.format("Key ID", "--key_id")
        assert secret_key, no_key_msg.format("Secret Key", "--secret_key")
    else:
        raise Exception('Invalid Scalr API level')

    return api_key_id, secret_key


def request(method, api_level, request_uri, payload=None, data=None):
    """
    Makes request to Scalr API.
    """

    time_iso8601 = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())

    try:
        api_key_id, secret_key = _key_pair(api_level=api_level)

        query_string = urlencode(
            sorted(payload.items()),
            quote_via=quote
        ) if payload else ''

        body = json.dumps(yaml.safe_load(data)) if data else ''  # XXX

        string_to_sign = '\n'.join((
            method.upper(),
            time_iso8601,
            request_uri,
            query_string,
            body
        ))

        digest = hmac.new(
            secret_key.encode('UTF-8'),
            string_to_sign.encode('UTF-8'),
            hashlib.sha256
        ).digest()

        signature = '{} {}'.format(
            settings.SIGNATURE_VERSION,
            binascii.b2a_base64(digest).strip().decode('UTF-8')
        )

        headers = dict()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        headers['X-Scalr-Key-Id'] = api_key_id
        headers['X-Scalr-Date'] = time_iso8601
        headers['X-Scalr-Signature'] = signature
        # if hasattr(settings, "API_DEBUG") and settings.API_DEBUG:
        #    headers['X-Scalr-Debug'] = 1

        url = urlunsplit((
            settings.API_SCHEME,
            settings.API_HOST,
            request_uri,
            '',
            ''
        ))

        if settings.debug_mode:
            click.echo('API HOST: {}\n'
                       'stringToSign: {}\n'
                       'Headers: {}\n'.format(
                           settings.API_HOST,
                           string_to_sign,
                           json.dumps(headers, indent=2))
                       )

        resp = requests.request(
            method.lower(),
            url,
            data=body,
            params=payload,
            headers=headers,
            verify=settings.SSL_VERIFY_PEER
        )
        result = resp.text

    except (Exception, BaseException) as e:
        if settings.debug_mode:
            raise
        raise click.ClickException(str(e))
    return result
