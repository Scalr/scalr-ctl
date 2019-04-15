# -*- coding: utf-8 -*-
"""
OpenAPI core classes
"""
import abc
import typing

from six.moves.urllib import parse
import six

from scalrctl import click, utils


@six.add_metaclass(abc.ABCMeta)
class OpenAPIBaseSpec(object):
    """
    General Base specification interface
    """
    raw_spec = None
    _discriminators = {}  # type: dict

    def __init__(self, raw_spec):
        self.raw_spec = raw_spec

    @abc.abstractmethod
    def base_path(self):
        """
        Base method for getting path.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_response_ref(self, route, http_method):
        """
        Base method for getting response reference.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_body_type_params(self, route, http_method):
        """
        Base method for getting body type params.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_path_type_params(self, route):
        """
        Base method for getting path type params.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_iterable_object(self, route, http_method):
        """
        Base method for return iterable.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_default_options(self, route, http_method):
        """
        Base method for getting default options.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_column_names(self, route, http_method, obj_type=None):
        """
        Base method for getting column names.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def filter_json_object(self, data, route, http_method, filter_createonly=False,
                           schema=None, reference=None):
        """
        Base method for getting json object.
        """
        raise NotImplementedError()

    def lookup(self, response_ref):
        # type: (str) -> str
        """
        Returns document section
        Example: #/definitions/Image returns Image defenition section.
        """
        return utils.lookup(response_ref, self.raw_spec)

    def get_raw_params(self, route, http_method):
        # type: ('str', 'str') -> typing.List[str]
        """
        Return list of body type params.
        """
        result = self.get_path_type_params(route)
        if http_method.upper() in ('GET', 'DELETE'):
            body_param = self.get_body_type_params(route, http_method)
            if body_param:
                result.append(body_param)
        return result

    def result_descr(self, route, http_method):
        # type: (str, str) -> dict
        """
        Return document section for reference.
        """
        ref = self.get_response_ref(route, http_method)
        return self.lookup(ref) if ref else {}

    def list_concrete_types(self, schema):
        """
        Get document section for reference.
        """
        types = []
        if "x-concreteTypes" in schema:
            for ref_dict in schema["x-concreteTypes"]:
                ref_link = ref_dict['$ref']
                types += [link.split("/")[-1] for link in
                          self.list_concrete_types_recursive(ref_link)]
        return types

    def list_concrete_types_recursive(self, reference):
        """
        Get list of x-concreteTypes values.
        """
        references = []
        schema = self.lookup(reference)
        if "x-concreteTypes" not in schema:
            references.append(reference)
        else:
            for ref_dict in schema["x-concreteTypes"]:
                references += self.list_concrete_types_recursive(ref_dict['$ref'])
        return references


class OpenAPIv2Spec(OpenAPIBaseSpec):
    """
    Class for OpenAPI2 Specification.
    """

    @property
    def base_path(self):
        """
        Get base path for OpenAPI2.
        """
        return self.raw_spec["basePath"]

    def get_response_ref(self, route, http_method):
        """
        Get response reference for OpenAPI2.
        """
        route_data = self.raw_spec['paths'][route]
        responses = route_data[http_method]['responses']
        response_code = utils.SUCCESS_CODES[http_method]
        if response_code in responses:
            response_200 = responses[response_code]
            if 'schema' in response_200:
                schema = response_200['schema']
                if '$ref' in schema:
                    response_ref = schema['$ref']
                    return response_ref

    def get_body_type_params(self, route, http_method):
        """
        Get body type params for OpenAPI2.
        """
        route_data = self.raw_spec['paths'][route][http_method]
        data = route_data.get('parameters', [])
        if data:
            return dict(
                schema=data[0].get('schema'),
                required=data[0].get('required'),
                description=data[0].get('description'),
                name=[data[0].get('name')]
            )
        return {}

    def get_path_type_params(self, route):
        # type: (str) -> typing.List[str]
        """
        Get path type params for OpenAPI2.
        """
        route_data = self.raw_spec['paths'][route]
        params = [param for param in route_data.get('parameters', '')]
        return params

    def get_iterable_object(self, route, http_method):
        """
        Checking object if it is an array.
        """
        result = False
        responses = self.raw_spec['paths'][route][http_method]['responses']
        response_code = utils.SUCCESS_CODES[http_method]
        if response_code in responses:
            response_200 = responses.get(response_code)
            if 'schema' in response_200:
                schema = response_200['schema']
                if '$ref' in schema:
                    object_key = schema['$ref'].split('/')[-1]
                    object_descr = self.raw_spec['definitions'][object_key]
                    object_properties = object_descr['properties']
                    data_structure = object_properties['data']
                    result = data_structure.get('type') == 'array'
        return result

    def get_default_options(self, route, http_method):
        """
        Get default options.
        """
        options = []
        for param in self.get_raw_params(route, http_method):
            option = click.Option(('--{}'.format(param['name']),
                                  param['name']), required=param['required'],
                                  help=param['description'],
                                  default=param.get('default'),
                                  show_default='default' in param)
            options.append(option)
        return options

    def get_column_names(self, route, http_method, obj_type=None):
        """
        Get columns names.
        """
        data = self.result_descr(route, http_method)['properties']['data']
        response_ref = data['items']['$ref'] \
            if 'items' in data else data['$ref']
        response_descr = self.lookup(response_ref)
        properties = response_descr['properties']

        column_names = []
        for k, v in properties.items():
            if '$ref' not in v:
                column_names.append(k)
            else:  # ST-226
                f_key = self.lookup(v['$ref'])
                if "properties" in f_key:
                    if len(f_key["properties"]) == 1 and \
                            f_key.get("properties", {}).get("id", {}).get("type") in \
                       ("integer", "string"):
                        column_names.append("%s.id" % k)
        return column_names

    def _get_schema(self, route, http_method):
        # type: (str, str) -> str
        """
        Get schema from route.
        """
        schema = None
        param = self.get_body_type_params(route, http_method)
        if 'schema' in param:
            schema = param['schema']
            if '$ref' in schema:
                schema = self.lookup(schema['$ref'])
        return schema

    def filter_json_object(self, data, route, http_method, filter_createonly=False,
                           schema=None, reference=None):
        """
        Removes immutable parts from JSON object
        before sending it in POST or PATCH.
        """

        filtered = {}

        # load `schema`
        if schema is None:
            schema = self._get_schema(route, http_method)

        # load child object as `schema`
        if 'discriminator' in schema:
            disc_key = schema['discriminator']
            disc_path = '{}/{}'.format(reference, disc_key)
            disc_value = data.get(disc_key) or self._discriminators.get(disc_path)

            if not disc_value:
                raise click.ClickException((
                    "Provided JSON object is incorrect: missing required param '{}'."
                ).format(disc_key))
            elif disc_value not in self.list_concrete_types(schema):
                raise click.ClickException((
                    "Provided JSON object is incorrect: required "
                    "param '{}' has invalid value '{}', must be one of: {}."
                ).format(disc_key, disc_value, self.list_concrete_types(schema)))
            else:
                # save discriminator for current reference/key
                self._discriminators[disc_path] = disc_value

            reference = '#/definitions/{}'.format(disc_value)
            schema = self.lookup(reference)

        # filter input data by properties of `schema`
        if schema and 'properties' in schema:
            create_only_props = schema.get('x-createOnly', '')
            for p_key, p_value in schema['properties'].items():
                if reference:
                    key_path = '.'.join([reference.split('/')[-1], p_key])
                else:
                    key_path = p_key

                if p_key not in data:
                    utils.debug("Ignore {}, unknown key.".format(key_path))
                    continue
                if p_value.get('readOnly'):
                    utils.debug("Ignore {}, read-only key.".format(key_path))
                    continue
                if filter_createonly and p_key in create_only_props:
                    utils.debug("Ignore {}, create-only key.".format(key_path))
                    continue

                if '$ref' in p_value and isinstance(data[p_key], dict):
                    # recursive filter sub-object
                    utils.debug("Filter sub-object: {}.".format(p_value['$ref']))
                    filtered[p_key] = self.filter_json_object(
                        data[p_key],
                        route,
                        http_method,
                        filter_createonly=filter_createonly,
                        reference=p_value['$ref'],
                        schema=self.lookup(p_value['$ref']),
                    )
                else:
                    # add valid key-value
                    filtered[p_key] = data[p_key]
        return filtered


class OpenAPIv3Spec(OpenAPIBaseSpec):
    """
    OpenAPI3 class representation.
    """

    @property
    def base_path(self):
        """
        Get base path for OpenAPI3.
        """
        servers = self.raw_spec["servers"]
        default_server = servers[0]
        result = default_server["url"]
        path = parse.urlsplit(result).path
        return path[:-1]

    def get_response_ref(self, route, http_method):
        """
        Get response reference for OpenAPI3.
        """
        responses = self.raw_spec['paths'][route][http_method]['responses']
        response_200 = responses.get(utils.SUCCESS_CODES[http_method])
        if '$ref' in response_200:
            response_200 = self.lookup(response_200['$ref'])
        result = response_200['content']['application/json']['schema']['$ref']
        return result

    def get_body_type_params(self, route, http_method):
        """
        Get body type of params for OpenAPI3.
        """

        def list_references_oneof(data):
            '''
            returns a list of full references to objects inside oneOf block
            '''
            list_typedata = data['oneOf']
            list_refs = []
            for type_dict in list_typedata:
                if '$ref' in type_dict:
                    list_refs.append(type_dict['$ref'])
            return list_refs

        route_data = self.raw_spec['paths'][route][http_method]
        if "requestBody" in route_data:
            param = {}
            request_body = route_data['requestBody']
            raw_block = self.lookup(request_body.get("$ref")) if "$ref" in \
                    request_body else request_body
            param["schema"] = raw_block["content"]['application/json']["schema"]
            param["required"] = raw_block.get("required")
            param["description"] = raw_block.get("description")
            schema = param["schema"]

            if '$ref' in schema:
                param["name"] = [raw_block.get("name", schema['$ref'].split('/')[-1]), ]
            elif 'oneOf' in schema:
                param["name"] = [ref.split('/')[-1] for ref in list_references_oneof(schema)]

            return param
        return {}

    def get_path_type_params(self, route):
        # type: (str) -> typing.List[dict]
        """
        Get path type params for OpenAPI3.
        """
        route_data = self.raw_spec['paths'][route]
        params = []
        for param in route_data.get('parameters', ''):
            if '$ref' in param:
                obj = self.lookup(param['$ref'])
                params.append(obj)
            else:
                params.append(param)
        return params

    def get_iterable_object(self, route, http_method):
        """
        Return bool values if values is array.
        """
        responses = self.raw_spec['paths'][route]['get']['responses']
        if utils.SUCCESS_CODES[http_method] in responses:
            response_200 = responses.get(utils.SUCCESS_CODES[http_method])
            if "$ref" in response_200:
                response_200 = self.lookup(response_200['$ref'])
            if 'schema' in response_200["content"]["application/json"]:
                schema = response_200["content"]["application/json"]["schema"]
                if '$ref' in schema:
                    schema = self.lookup(schema["$ref"])
                object_properties = schema['properties']
                data_structure = object_properties['data']
                result = data_structure.get('type') == 'array'
                return result
        return False

    def get_default_options(self, route, http_method):
        """
        Get default options for OpenAPI3.
        """
        options = []
        for param in self.get_raw_params(route, http_method):
            option = click.Option(('--{}'.format(param['name']),
                                  param['name']), required=param['required'],
                                  help=param['description'],
                                  default=param.get('default'),
                                  show_default='default' in param)
            options.append(option)
        return options

    def get_column_names(self, route, http_method, obj_type=None):
        """
        Get column names for determine routes.
        """
        column_names = []
        data = self.result_descr(route, http_method)['properties']['data']
        if 'items' in data:
            items = data['items']
            if 'oneOf' in items:
                response_ref = utils.handle_oneof(items, obj_type)
                if not response_ref:
                    return column_names
            else:
                response_ref = items['$ref']
        elif '$ref' in data:
            response_ref = data['$ref']
        elif 'oneOf' in data:
            response_ref = utils.handle_oneof(data, obj_type)
        response_descr = self.lookup(response_ref)
        if 'allOf' in response_descr:
            properties = self._merge_all(response_descr).get('properties', {})
        else:
            properties = response_descr.get('properties', {})

        for k, v in properties.items():
            if '$ref' not in v:
                column_names.append(k)
            else:  # ST-226
                f_key = self.lookup(v['$ref'])
                if "properties" in f_key and len(f_key["properties"]) == 1 and "id" in\
                   f_key["properties"] and "type" in f_key["properties"]["id"]:
                        if f_key["properties"]["id"]["type"] in ("integer", "string"):
                            column_names.append("%s.id" % k)
        return column_names

    def _merge_all(self, data):
        """
        Merge objects into one if 'allOf' in schema.
        """
        return utils.merge_all(data, self.raw_spec)

    def _get_schema(self, route, http_method):
        # type: (str, str) -> str
        """
        Get schema from route.
        """
        schema = None
        param = self.get_body_type_params(route, http_method)
        if 'schema' in param:
            schema = param['schema']
            if '$ref' in schema:
                schema = self.lookup(schema['$ref'])
        return schema

    def filter_json_object(self, data, route, http_method, filter_createonly=False,
                           schema=None, reference=None):
        """
        Removes immutable parts from JSON object
        before sending it in POST or PATCH.
        """
        filtered = {}

        # load `schema`
        if schema is None:
            schema = self._get_schema(route, http_method)

        # load child object as `schema`
        if 'discriminator' in schema:
            disc_key = schema.get("discriminator").get('propertyName')  #
            disc_path = '{}/{}'.format(reference, disc_key)
            disc_value = data.get(disc_key) or self._discriminators.get(disc_path)

            if not disc_value:
                raise click.ClickException((
                    "Provided JSON object is incorrect: missing required param '{}'."
                ).format(disc_key))

            reference = '#/components/schemas/{}'.format(disc_value)
            schema = self.lookup(reference)
            if "allOf" in schema:
                schema = self._merge_all(schema)

            if disc_value not in self.list_concrete_types(schema):
                raise click.ClickException((
                    "Provided JSON object is incorrect: required "
                    "param '{}' has invalid value '{}', must be one of: {}."
                ).format(disc_key, disc_value, self.list_concrete_types(schema)))
            else:
                # save discriminator for current reference/key
                self._discriminators[disc_path] = disc_value

        # filter input data by properties of `schema`
        if schema and 'properties' in schema:
            create_only_props = schema.get('x-createOnly', '')
            for p_key, p_value in schema['properties'].items():
                if reference:
                    key_path = '.'.join([reference.split('/')[-1], p_key])
                else:
                    key_path = p_key

                if p_key not in data:
                    utils.debug("Ignore {}, unknown key.".format(key_path))
                    continue
                if p_value.get('readOnly'):
                    utils.debug("Ignore {}, read-only key.".format(key_path))
                    continue
                if filter_createonly and p_key in create_only_props:
                    utils.debug("Ignore {}, create-only key.".format(key_path))
                    continue

                if '$ref' in p_value and isinstance(data[p_key], dict):
                    # recursive filter sub-object
                    utils.debug("Filter sub-object: {}.".format(p_value['$ref']))

                    sub_schema = self.lookup(p_value['$ref'])
                    if "allOf" in sub_schema:
                        sub_schema = self._merge_all(sub_schema)

                    filtered[p_key] = self.filter_json_object(
                        data[p_key],
                        route,
                        http_method,
                        filter_createonly=filter_createonly,
                        reference=p_value['$ref'],
                        schema=sub_schema,
                    )
                else:
                    # add valid key-value
                    filtered[p_key] = data[p_key]
        return filtered

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
