# -*- coding: utf-8 -*-
import json
import os
import pytest
import requests

from scalrctl import defaults, commands, utils

if defaults.OPENAPI_ENABLED:
    spec = commands.get_spec(utils.read_spec_openapi())
else:
    spec = commands.get_spec(utils.read_spec("user", ext='json'))

def test_get_body_type_params():
    if defaults.OPENAPI_ENABLED:
        route = "/user/{envId}/scripts/{scriptId}/"
    else:
        route = "/{envId}/scripts/{scriptId}/"
    params = spec.get_body_type_params(route, http_method="patch")[0]
    #print params
    assert 'required' in params
    assert params['required']
    assert 'description' in params
    assert 'schema' in params
    assert 'name' in params

    if not defaults.OPENAPI_ENABLED:  # XXX
        assert params['name'].endswith('Object')
        assert 'in' in params



def _test_test():
    '''    
    action = commands.Action(name="update",
                             route="/{envId}/scripts/{scriptId}/",
                             http_method="patch",
                             api_level="user")
    '''
    pass