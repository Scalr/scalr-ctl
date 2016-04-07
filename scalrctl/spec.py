__author__ = 'Dmitriy Korsakov'

import os
import json

from scalrctl import settings


class MetaSpec(object):

    specs = None

    def __init__(self, *specs):
        with open(os.path.join(os.path.dirname(__file__), 'scheme/scheme.json')) as fp:
            self.data = json.load(fp)
        self.specs = specs

    def __repr__(self):
        return str([spec_dict["basePath"] for spec_dict in self.specs])

    @classmethod
    def lookup(cls, base_path=None, api_levels=None):
        if not base_path:
            base_path = os.path.expanduser(os.environ.get("SCALRCLI_HOME", "~/.scalr"))

        if not api_levels:
            api_levels = ["user", "account", "admin"]

        data = []

        for api_level in api_levels:
            path = os.path.join(base_path, "%s.json" % api_level)
            if os.path.exists(path):
                spec_dict = json.load(open(path, "r"))
                data.append(spec_dict)

        return cls(*data)

    def get_route(self, command_name, subcommand_name, api_level="user"):
        return self.data[api_level][command_name]["subcommands"][subcommand_name]['route']

    def get_http_method(self, command_name, subcommand_name, api_level="user"):
        return self.data[api_level][command_name]["subcommands"][subcommand_name]['http-method']

    def list_http_methods(self, route):
        methods = []
        return methods

    def get_command_name(self, route, method):
        name = []
        return name

    def get_command_object(self, command_name, subcommand_name, api_level="user"):
        obj = None
        return obj

    def list_options(self, command_name, subcommand_name, api_level="user"):
        pass


    def _get_spec_dict(self, api_level="user"):
        for spec in self.specs:
            if api_level in spec["basePath"]:
                return spec

    def _list_cmd_aliases(self, api_level="user"):
        """return route aliases"""
        level_data = self.data[api_level]
        return [alias for alias in level_data if alias]

    def _get_cmd_descr(self, command_name, api_level="user"):
        "returns help for command e.g. OS help"
        level_data = self.data[api_level]
        cmd_data = level_data[command_name]
        return cmd_data["descr"]

    def _get_subcmd_descr(self, command_name, subcommand_name, api_level="user"):
        "returns help for command e.g. OS help"
        level_data = self.data[api_level]
        cmd_data = level_data[command_name]
        return cmd_data["descr"]

    def _list_subcmd_aliases(self, command_name, api_level="user"):
        """returns aliases for subcommands (route+http_method)"""
        return self.data[api_level][command_name]["subcommands"].keys()


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
        responses = self._data['responses']
        if '200' in responses:
            ok200 = responses['200']
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

def get_raw_spec(api_level="user"):
    api_level = api_level or "user"  #XXX: Ugly,  SubCommand class needs to be changed first
    path = os.path.join(os.path.expanduser(os.environ.get("SCALRCLI_HOME", "~/.scalr")), "%s.json" % api_level)
    if os.path.exists(path):
        return json.load(open(path, "r"))

def get_spec_url(api_level="user"):
    api_level = api_level or "user"  #XXX: Ugly,  SubCommand class needs to be changed first
    return "{0}://{1}/api/{2}.{3}.yml".format(settings.API_SCHEME, settings.API_HOST, api_level, settings.API_VERSION)