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
    raw_spec = {}  # type: typing.Dict[typing.Any, typing.Any]
    _discriminators = {}  # type: typing.Dict[typing.Any, typing.Any]

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
        # type: (str) -> dict
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
        response_ref = utils.get_response_ref_v2(self.raw_spec, route, http_method)
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
        route_data = self.raw_spec.get('paths', {}).get(route, {})
        params = [param for param in route_data.get('parameters', '')]
        return params

    def get_iterable_object(self, route, http_method):
        """
        Checking object if it is an array.
        """
        responses = self.raw_spec['paths'][route][http_method]['responses']
        result = utils.check_iterable_v2(responses, route, http_method,
                                         self.raw_spec)
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
        column_names = utils.get_column_names_v2(data, route, http_method,
                                                 self.raw_spec, obj_type=obj_type)
        return column_names

    def _get_schema(self, route, http_method):
        # type: (str, str) -> dict
        """
        Get OpenAPI2 schema from route.
        """
        schema = {}  # type: dict
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
        result = utils.get_response_ref_v3(self.raw_spec, route, http_method)
        return result

    def get_body_type_params(self, route, http_method):
        """
        Get body type of params for OpenAPI3.
        """

        param = utils.get_body_type_params_v3(self.raw_spec, route, http_method)
        return param

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
        Return bool value if column type is array.
        """
        responses = self.raw_spec['paths'][route]['get']['responses']
        result = utils.check_iterable_v3(responses, route, http_method,
                                         self.raw_spec)
        return result

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
        data = self.result_descr(route, http_method)['properties']['data']
        column_names = utils.get_column_names_v3(data, route, http_method,
                                                 self.raw_spec, obj_type=obj_type)
        return column_names

    def _merge_all(self, data):
        # type: (typing.List[dict]) -> dict
        """
        Merge objects into one if ['allOf', 'anyOf', ...] in schema.
        """
        return utils.merge_all(data, self.raw_spec)

    def _get_schema(self, route, http_method):
        # type: (str, str) -> dict
        """
        Get OpenAPI3 schema from route.
        """
        schema = {}  # type: dict
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
