# -*- coding: utf-8 -*-
import json

import pytest
import requests

from scalrctl import defaults, examples


@pytest.fixture(scope="module")
def specs():
    data = {}
    for api_level in defaults.API_LEVELS:
        data[api_level] = json.loads(examples._read_spec(api_level))
    return data


@pytest.fixture(scope="module")
def post_endpoints(specs):
    endpoints = []
    for api_level, spec_data in specs.items():
        for endpoint, params_spec in spec_data['paths'].items():
            if 'post' in params_spec:
                endpoints.append((api_level, endpoint))
    return endpoints


def _is_valid_endpoint(endpoint):
    return not ('/actions/' in endpoint or endpoint in examples.EXCLUDES)


def test_create_post_example(post_endpoints):
    for api_level, endpoint in post_endpoints:
        try:
            examples.create_post_example(api_level, endpoint)
        except Exception as e:
            assert not _is_valid_endpoint(endpoint) \
                   and e.message == 'Invalid API endpoint'
        else:
            assert _is_valid_endpoint(endpoint)


def test_get_object_name(specs, post_endpoints):
    for api_level, endpoint in post_endpoints:
        if _is_valid_endpoint(endpoint):
            object_name = examples.get_object_name(specs[api_level], endpoint)
            doc_url = examples.get_doc_url(api_level, endpoint)
            resp = requests.get(doc_url)
            assert resp.status_code == 200
            assert '<p>The JSON representation of a {} ' \
                   'object.</p>'.format(object_name) in resp.text
