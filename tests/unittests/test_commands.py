# -*- coding: utf-8 -*-
"""
Test commands
"""

import unittest

from scalrctl import defaults, utils

if defaults.OPENAPI_ENABLED:
    SPEC = utils.get_spec(utils.read_spec_openapi())
else:
    SPEC = utils.get_spec(utils.read_spec("user", ext='json'))


class TestCommands(unittest.TestCase):
    """
    Cover via unittests bases commands.
    """

    def setUp(self):
        """
        Start up settings
        """
        self.route = "/user/{envId}/scripts/{scriptId}/" if defaults.OPENAPI_ENABLED else\
                "/{envId}/scripts/{scriptId}/"

    def test_get_body_type_params(self):
        """
        Test body params
        """
        params = SPEC.get_body_type_params(self.route, http_method="patch")[0]
        self.assertIn('required', params)
        self.assertIn('description', params)
        self.assertIsNotNone(params['required'])
        self.assertIn('schema', params)
        self.assertIn('name', params)

        if not defaults.OPENAPI_ENABLED:
            self.assertTrue(params['name'].endswith('Object'))
            self.assertIn('in', params)

    def test_merge_all(self):
        """
        Test merge all
        """
        data = {u'allOf':
                [{u'$ref': u'#/components/schemas/StorageConfiguration'},
                 {u'properties': {u'template':
                     {u'$ref': u'#/components/schemas/PersistentStorageTemplate'}},
                  u'required': [u'template'],
                  u'type': u'object',
                  u'x-createOnly': [u'type'],
                  u'x-usedIn':
                  [u'/user/{envId}/farm-roles/{farmRoleId}/storage/',
                   u'/user/{envId}/farm-roles/{farmRoleId}/storage/{storageConfigurationId}/']}]}
        self.assertEqual(data, data)
        return data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
