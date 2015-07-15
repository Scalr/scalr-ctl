__author__ = 'Dmitriy Korsakov'

import os
import json

import settings

class Spec(object):

    document = None
    method = None
    route = None


    def __init__(self, document, route, method):
        self.document = document
        self.route = route
        self.method = method


    @property
    def _route_data(self):
        return self.document["paths"][self.route]

    @property
    def _data(self):
        return self._route_data[self.method]

    @property
    def _result_descr(self):
        responces = self._data['responses']
        if '200' in responces:
            ok200 = responces['200']
            if 'schema' in ok200:
                schema = ok200['schema']
                if '$ref' in schema:
                    reference = schema['$ref']
                    return self.lookup(reference)

    @property
    def description(self):
        return self._data['description'] if 'description' in self._data else ''

    @property
    def method_params(self):
        params = []
        if "parameters" in self._data:
            for parameter in self._data['parameters']:
                params.append(parameter)
        return params

    @property
    def route_params(self):
        return self._route_data['parameters']

    def returns_iterable(self):
        if "GET" != self.method.upper():
            return False

        object_properties = self._result_descr["properties"]
        data_structure = object_properties["data"]
        if "type" in data_structure:
            responce_type = data_structure["type"]
            if "array" == responce_type:
                return True
        return False

    @property
    def filters(self):
        if self.returns_iterable():
            response_ref = self._result_descr["properties"]["data"]["items"]["$ref"]
            response_descr = self.lookup(response_ref)
            if "x-filterable" in response_descr:
                filters = response_descr["x-filterable"]
                return filters
        return []

    def lookup(self, refstr):
        """
        Returns document section
        Example: #/definitions/Image returns Image defenition section
        """
        if refstr.startswith("#"):
            paths = refstr.split("/")[1:]
            result = self.document
            for path in paths:
                if path not in result:
                    return
                result = result[path]
            return result

    def get_column_names(self):
        fields = []
        data = self._result_descr["properties"]["data"]
        # response_ref = data["items"]["$ref"] if "items" in data else data["$ref"] # [ST-54]
        response_ref = data["items"]["$ref"]
        response_descr = self.lookup(response_ref)
        for k,v in response_descr["properties"].items():
            if "$ref" not in v:
                fields.append(k)
        return sorted(fields)

    def __repr__(self):
        return 'Spec("%s", "%s")' % (self.route, self.method)

def get_raw_spec():
    path = os.path.join(os.path.expanduser(os.environ.get("SCALRCLI_HOME", "~/.scalr")), "user.json")
    if os.path.exists(path):
        return json.load(open(path, "r"))

def get_spec_url(api_level="user"):
    return "{0}://{1}/api/{2}.{3}.yml".format(settings.API_SCHEME, settings.API_HOST, api_level, settings.API_VERSION)