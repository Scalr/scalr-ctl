# -*- coding: utf-8 -*-
import json
import abc
import re
import os
import time

from itertools import chain
from collections import defaultdict

import dicttoxml

from scalrctl import click, request, settings, utils, view, examples, defaults

import six
from six.moves.urllib import parse

__author__ = 'Dmitriy Korsakov'


success_codes = {
    'get': '200',
    'post': '201',
    'delete': '204',
    'patch': '200',
}


class MultipleClickException(click.ClickException):

    def format_message(self):
        return '\x1b[31m%s\x1b[39m' % self.message if settings.colored_output else self.message

    def show(self, file=None):
        if file is None:
            file = click._compat.get_text_stderr()
        click.utils.echo('%s' % self.format_message(), file=file)


class BaseAction(object):

    epilog = None

    def __init__(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        pass

    def get_description(self):
        return ''

    def modify_options(self, options):
        return options

    def get_options(self):
        return []

    def validate(self):
        pass


class Action(BaseAction):

    raw_spec = None

    # Optional. Some values like GCE imageId
    # cannot be passed through command lines
    prompt_for = None

    # Temporary. Object definitions in YAML
    # spec are not always correct
    mutable_body_parts = None

    # Optional, e.g. '#/definitions/GlobalVariable'
    object_reference = None

    dry_run = False
    post_template = None
    _table_columns = []

    _discriminators = {}

    ignored_options = ()
    delete_target = None

    def __init__(self, name, route, http_method, api_level, *args, **kwargs):
        self.name = name
        self.route = route
        self.http_method = http_method
        self.api_level = api_level
        self.strip_metadata = False

        self._init()

    def _init(self):
        if defaults.OPENAPI_ENABLED:
            self.spec = get_spec(utils.read_spec_openapi())
        else:
            self.spec = get_spec(utils.read_spec(self.api_level, ext='json'))


        if not self.epilog and self.http_method.upper() == 'POST':
            msg = "Example: scalr-ctl {level} {name} < {name}.json"
            self.epilog = msg.format(
                level=self.api_level if self.api_level != 'user' else '',
                name=self.name
            )

    def _check_arguments(self, **kwargs):
        route_data = self.spec.raw_spec['paths'][self.route]
        if 'parameters' not in route_data:
            return

        for param in route_data['parameters']:
            pattern = param.get('pattern')
            param_name = param.get('name')
            if pattern and param_name and param_name in kwargs:
                value = str(kwargs[param_name])
                matches = re.match(pattern, value.strip())
                if not matches or len(matches.group()) != len(value):
                    raise click.ClickException("Invalid value for {}"
                                               .format(param_name))

    def _apply_arguments(self, **kwargs):
        if kwargs.get('filters'):
            for pair in kwargs.pop('filters').split(','):
                kv = pair.split('=')
                if len(kv) == 2:
                    kwargs[kv[0]] = kv[1]

        if kwargs.get('columns'):
            self._table_columns = kwargs.pop('columns').split(',')

        if kwargs.pop('strip_metadata', False):
            self.strip_metadata = True

        if kwargs.pop('dryrun', False):
            self.dry_run = True

        if kwargs.pop('debug', None):
            settings.debug_mode = True

        if kwargs.pop('nocolor', None):
            settings.colored_output = False

        if kwargs.get('transformation'):
            settings.view = kwargs.pop('transformation')

        return kwargs

    def _get_object_as_text(self, filter_createonly=True, *args, **kwargs):
        try:
            obj = self.__class__(name='get', route=self.route,
                                 http_method='get', api_level=self.api_level)
            raw_text = obj.run(*args, **kwargs)
            utils.debug(raw_text)
            if raw_text is None:
                return {}
            json_dict = json.loads(raw_text)
            if filter_createonly:
                filtered = self.spec.filter_json_object(json_dict['data'],
                                                        self.route,
                                                        self.http_method,
                                                        filter_createonly=True)
                return json.dumps(filtered, indent=2)
            return json.dumps(json_dict['data'], indent=2)
        except Exception as e:
            utils.reraise(e)

    def _edit_object(self, *args, **kwargs):
        raw_object = self._get_object(*args, **kwargs)
        raw_object = click.edit(raw_object)
        if raw_object is None:
            raise ValueError("No changes in JSON")
        return json.loads(raw_object)

    def _edit_example(self):
        commentary = examples.create_post_example(self.api_level, self.route)
        text = click.edit(commentary)
        if text:
            raw_object = "".join([line for line in text.splitlines()
                                  if not line.startswith("#")]).strip()
        else:
            raw_object = ""
        return json.loads(raw_object)

    @staticmethod
    def _read_object():
        """
        Reads JSON object from stdin.
        """
        raw_object = click.get_text_stream('stdin').read()
        return json.loads(raw_object)

    def _format_errmsg(self, errors):
        messages = []
        num = 1
        for error_data in errors:
            err_code = '%s:' % error_data['code'] if 'code' in error_data else ''
            err_msg = error_data.get('message', '')
            err_index = ':' if len(errors) == 1 else ' %s:' % num
            err_line = 'Error%s %s %s' % (err_index, err_code, err_msg)
            messages.append(err_line)
            num += 1
        result_errmsg = '\n'.join(messages)
        return result_errmsg

    def get_response_type(self, response_dict):
        obj_type = None
        data = response_dict['data']
        if isinstance(data, dict):
            if 'type' in data:
                obj_type = data['type']
        elif isinstance(data, list):
            if data and data[0]:
                obj_type = data[0].get('type')
        return obj_type

    def _format_response(self, response, hidden=False, **kwargs):
        text = None

        if response:
            try:
                response_json = json.loads(response)
            except ValueError:
                utils.debug("Server response: {}".format(str(response)))
                utils.reraise("Invalid server response")

            errors = response_json.get('errors')

            if errors:
                errmsg = self._format_errmsg(errors)
                error = MultipleClickException(errmsg)
                error.code = 1
                raise error

            if not hidden:
                utils.debug(response_json.get('meta'))

            if self.strip_metadata and self.http_method.upper() == 'GET' and \
                    settings.view in ('raw', 'json', 'xml') and 'data' in response_json:  # SCALRCORE-10392
                response_json = response_json['data']
                response = json.dumps(response_json)

            if hidden:
                pass
            elif settings.view in ('raw', 'json'):
                click.echo(response)
            elif settings.view == 'xml':
                click.echo(dicttoxml.dicttoxml(response_json))
            elif settings.view == 'tree':
                data = json.dumps(response_json.get('data'))
                click.echo(view.build_tree(data))
            elif settings.view == 'table':
                obj_type = self.get_response_type(response_json)
                columns = self._table_columns or self.spec.get_column_names(self.route, self.http_method, obj_type)
                if self.spec.returns_iterable(self.route, self.http_method):
                    rows, current_page, last_page = view.calc_vertical_table(response_json,
                                                                    columns)
                    pre = "Page: {} of {}".format(current_page, last_page)
                    click.echo(view.build_vertical_table(columns, rows, pre=pre))
                else:
                    click.echo(view.build_horizontal_table(
                        view.calc_horizontal_table(response_json, columns)))

        elif self.http_method.upper() == 'DELETE':
            deleted_id = kwargs.get(self.delete_target, '') or ''
            if not deleted_id:
                for param, value in kwargs.items():
                    if 'Id' in param and param not in ('envId', 'accountId'):
                        deleted_id = value
                        break
            if not deleted_id:
                for param, value in kwargs.items():
                    if 'Name' in param:
                        deleted_id = value
                        break
            text = "Deleted {}".format(deleted_id)
        return text

    def _get_default_options(self):
        options = []
        for param in self._get_raw_params():
            option = click.Option(('--{}'.format(param['name']),
                                  param['name']), required=param['required'],
                                  help=param['description'],
                                  default=param.get('default'),
                                  show_default='default' in param)
            options.append(option)
        return options

    def _get_custom_options(self):
        options = []

        if self.http_method.upper() in ('POST', 'PATCH'):
            stdin = click.Option(('--stdin', 'stdin'),
                                 is_flag=True, required=False,
                                 help="Read JSON data from standart console "
                                      "input instead of editing it in the "
                                      "default console text editor.")
            options.append(stdin)
            """
            interactive = click.Option(('--interactive', 'interactive'),
                                       is_flag=True, required=False,
                                       help="Edit JSON data in the default "
                                            "console text editor before "
                                            "sending POST request to server.")
            options.append(interactive)
            """

        if self.http_method.upper() == 'GET':
            if self.spec.returns_iterable(self.route, self.http_method):
                maxres = click.Option(('--max-results', 'maxResults'),
                                      type=int, required=False,
                                      help="Maximum number of records. "
                                      "Example: --max-results=2")
                options.append(maxres)

                pagenum = click.Option(('--page-number', 'pageNum'), type=int,
                                       required=False, help="Current page "
                                       "number. Example: --page-number=3")
                options.append(pagenum)

                filters = self._get_available_filters()
                if filters:
                    filters = sorted(filters)
                    filter_help = ("Apply filters. Example: type=ebs,size=8."
                                   "Available filters: {}."
                                   ).format(', '.join(filters))
                    filters = click.Option(('--filters', 'filters'),
                                           required=False, help=filter_help)
                    options.append(filters)

                columns_help = "Filter columns in table view [--table required]. Example: NAME,SIZE,SCOPE. "
                column_names = self.spec.get_column_names(self.route, self.http_method)
                if column_names:
                    columns_help += "Available columns: %s." % ', '.join(column_names)

                columns = click.Option(('--columns', 'columns'),
                                       required=False, help=columns_help)
                options.append(columns)

            raw = click.Option(('--raw', 'transformation'), is_flag=True,
                               flag_value='raw', default=False, hidden=True,
                               help="Print raw response")
            json_ = click.Option(('--json', 'transformation'), is_flag=True,
                                 flag_value='raw', default=False,
                                 help="Print raw response")
            strip_metadata = click.Option(('--no-envelope', 'strip_metadata'), is_flag=True, default=False,
                               help="Strip server response from all metadata.")
            xml = click.Option(('--xml', 'transformation'), is_flag=True,
                               flag_value='xml', default=False,
                               help="Print response as a XML")
            tree = click.Option(('--tree', 'transformation'), is_flag=True,
                                flag_value='tree', default=False,
                                help="Print response as a colored tree")
            nocolor = click.Option(('--nocolor', 'nocolor'), is_flag=True,
                                   default=False, help="Use colors")
            options += [raw, tree, nocolor, json_, xml, strip_metadata]

            if self.name not in ('get', 'retrieve'):  # [ST-54] [ST-102]
                table = click.Option(('--table', 'transformation'),
                                     is_flag=True, flag_value='table',
                                     default=False,
                                     help="Print response as a colored table")
                options.append(table)

        debug = click.Option(('--debug', 'debug'), is_flag=True,
                             default=False, help="Print debug messages")
        options.append(debug)

        return options

    def _get_body_type_params(self):
        route_data = self.raw_spec['paths'][self.route][self.http_method]
        return [param for param in route_data.get('parameters', '')]

    def _get_path_type_params(self):
        route_data = self.raw_spec['paths'][self.route]
        return [param for param in route_data.get('parameters', '')]

    def _get_raw_params(self):
        result = self._get_path_type_params()
        if self.http_method.upper() in ('GET', 'DELETE'):
            body_params = self._get_body_type_params()
            result.extend(body_params)
        return result

    def _returns_iterable(self):
        responses = self.raw_spec['paths'][self.route][self.http_method]['responses']
        if '200' in responses:
            response_200 = responses['200']
            if 'schema' in response_200:
                schema = response_200['schema']
                if '$ref' in schema:
                    object_key = schema['$ref'].split('/')[-1]
                    object_descr = self.raw_spec['definitions'][object_key]
                    object_properties = object_descr['properties']
                    data_structure = object_properties['data']
                    return 'array' == data_structure.get('type')
        return False

    def _get_available_filters(self):
        filters = []
        if self.spec.returns_iterable(self.route, self.http_method):
            data = self._result_descr['properties']['data']
            if "oneOf" in data['items']:
                return []
            response_ref = data['items']['$ref']
            response_descr = self.spec.lookup(response_ref)
            if 'x-filterable' in response_descr:
                filters = response_descr['x-filterable']
        return filters

    @property
    def _result_descr(self):
        return self.spec.result_descr(self.route, self.http_method)

    def _list_createonly_properties(self):
        """
        Some properties (mostly IDs) cannot be marked as read-only because
        they are passed in PUT-methods (but still must be filtered in
        UPDATE-methods).
        """
        result_descr = self._result_descr
        if result_descr and 'properties' in result_descr:
            data = result_descr['properties']['data']
            if 'items' in data:
                path = data['items']['$ref']
            else:
                path = data['$ref']
            obj = self.spec.lookup(path)
            return obj['x-createOnly'] if 'x-createOnly' in obj else []

    @property
    def _request_template(self):
        return '{}{}'.format(self.spec.base_path, self.route)

    def pre(self, *args, **kwargs):
        """
        Before request is made.
        """
        kwargs = self._apply_arguments(**kwargs)
        self._check_arguments(**kwargs)

        import_data = kwargs.pop('import-data', {})
        stdin = kwargs.pop('stdin', None)
        http_method = self.http_method.upper()

        if http_method not in ('PATCH', 'POST'):
            return args, kwargs

        # prompting for body and then validating it

        param_names = []
        param_data = self.spec.get_body_type_params(self.route, self.http_method)
        param_name = param_data.get('name')
        if param_name: # XXX simplified actions might be affected, testing required
            param_names.extend(param_name)

        try:
            if import_data:
                for param_name in param_names:
                    if param_name in import_data:
                        raw_json_object = import_data[param_name]
                        filtered_json_object = self.spec.filter_json_object(
                            raw_json_object,
                            self.route,
                            self.http_method,
                            filter_createonly=True
                        ) if http_method == 'PATCH' else raw_json_object
            else:
                if http_method == 'PATCH':
                    if stdin:
                        self._get_object_as_text(*args, **kwargs)
                        raw_json_object = self._read_object()
                        filtered_json_object = self.spec.filter_json_object(raw_json_object,
                                                                            self.route,
                                                                            self.http_method)
                    else:
                        raw_text = self._get_object_as_text(filter_createonly=False, *args, **kwargs)
                        raw_json_object = json.loads(raw_text)

                        filtered_dict = self.spec.filter_json_object(
                            raw_json_object,
                            self.route,
                            self.http_method,
                            filter_createonly=True)
                        filtered_text = json.dumps(filtered_dict, indent=2)

                        editor_text = click.edit(filtered_text)
                        if editor_text is None:
                            raise ValueError("No changes in JSON")
                        filtered_json_object = json.loads(editor_text)

                elif http_method == 'POST':
                    if stdin:
                        raw_json_object = self._read_object()
                    else:
                        raw_json_object = self._edit_example()

                    filtered_json_object = self.spec.filter_json_object(
                        raw_json_object,
                        self.route,
                        self.http_method)

            schema = param_data['schema']
            if '$ref' in schema:
                reference = schema['$ref']
                schema = self.spec.lookup(schema['$ref'])

            if len(param_names) == 1: # XXX
                param_name = param_names[0]
            elif 'discriminator' in schema:
                disc_key = schema.get("discriminator").get('propertyName')
                param_name = raw_json_object.get(disc_key)
            kwargs[param_name] = filtered_json_object
        except ValueError as e:
            utils.reraise(e)
        return args, kwargs


    def post(self, response):
        """
        After request is made.
        """
        return response

    #
    # PUBLIC METHODS
    #

    def run(self, *args, **kwargs):
        """
        Callback for click subcommand.
        """
        hide_output = kwargs.pop('hide_output', False)  # [ST-88]
        args, kwargs = self.pre(*args, **kwargs)
        uri = self._request_template
        payload = {}
        data = {}

        if '{envId}' in uri and not kwargs.get('envId') and settings.envId:
            kwargs['envId'] = settings.envId

        if '{accountId}' in uri and not kwargs.get('accountId') and settings.accountId:
            kwargs['accountId'] = settings.accountId
        if kwargs:
            # filtering in-body and empty params
            uri = self._request_template.format(**kwargs)
            for key, value in kwargs.items():
                param = '{{{}}}'.format(key)
                if value and (param not in self._request_template):
                    body_params = self.spec.get_body_type_params(self.route, self.http_method)
                    if self.http_method.upper() in ('GET', 'DELETE'):
                        payload[key] = value
                    elif body_params and key in body_params['name']:
                        data.update(value)

        if self.dry_run:
            click.echo('{} {} {} {}'.format(self.http_method, uri,
                                            payload, data))
            # returns dummy response
            return json.dumps({'data': {}, 'meta': {}})

        data = json.dumps(data)
        raw_response = request.request(self.http_method, self.api_level,
                                       uri, payload, data)
        response = self.post(raw_response)
        text = self._format_response(response, hidden=hide_output, **kwargs)
        if text is not None:
            click.echo(text)

        return response

    def get_description(self):
        """
        Returns action description.
        """
        route_data = self.spec.raw_spec['paths'][self.route]
        return route_data[self.http_method]['description']

    def modify_options(self, options):
        """
        This is the place where command line options can be fixed
        after they are loaded from yaml spec.
        """
        for option in options:
            if self.prompt_for and option.name in self.prompt_for:
                option.prompt = option.name
            if (option.name == 'envId' and settings.envId) or \
                    (option.name == 'accountId' and settings.accountId):
                option.required = False
        return options

    def get_options(self):
        """
        Returns action options.
        """
        options = self.spec.get_default_options(self.route, self.http_method) + self._get_custom_options()
        return [opt for opt in options if opt.name not in self.ignored_options]

    def validate(self):
        """
        Validate routes for current API scope.
        """
        if self.route and self.api_level:
            fname = "openapi.json" if defaults.OPENAPI_ENABLED else '{}.json'.format(self.api_level)
            spec_path = os.path.join(defaults.CONFIG_DIRECTORY,
                                     fname)
            api_routes = json.load(open(spec_path, 'r'))['paths'].keys()
            try:
                assert api_routes and self.route in api_routes, self.name
            except AssertionError:  # ST-224
                if self.api_level == "account":
                    bc_route = self.route.replace('{accountId}/', '')
                    assert api_routes and bc_route in api_routes, self.name
                    self.route = bc_route
                else:
                    raise


class SimplifiedAction(Action):
    ignored_options = ('stdin',)


def get_spec(data):
    if utils.is_openapi_v3(data):
        return _OpenAPIv3Spec(data)
    else:
        return _OpenAPIv2Spec(data)


@six.add_metaclass(abc.ABCMeta)
class _OpenAPIBaseSpec(object):
    raw_spec = None
    _discriminators = {}

    def __init__(self, raw_spec):
        self.raw_spec = raw_spec

    @abc.abstractmethod
    def base_path(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_response_ref(self, route, http_method):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_body_type_params(self, route, http_method):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_path_type_params(self, route):
        raise NotImplementedError()

    @abc.abstractmethod
    def returns_iterable(self, route, http_method):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_default_options(self, route, http_method):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_column_names(self, route, http_method, obj_type=None):
        raise NotImplementedError()

    @abc.abstractmethod
    def filter_json_object(self, data, route, http_method, filter_createonly=False,
                            schema=None, reference=None):
        raise NotImplementedError()

    def lookup(self, response_ref):
        """
        Returns document section
        Example: #/definitions/Image returns Image defenition section.
        """
        return utils.lookup(response_ref, self.raw_spec)

    def get_raw_params(self, route, http_method):
        result = self.get_path_type_params(route)
        if http_method.upper() in ('GET', 'DELETE'):
            body_param = self.get_body_type_params(route, http_method)
            if body_param:
                result.append(body_param)
        return result

    def result_descr(self, route, http_method):
        ref = self.get_response_ref(route, http_method)
        if ref:
            return self.lookup(ref)

    def list_concrete_types(self, schema):
        types = []
        if "x-concreteTypes" in schema:
            for ref_dict in schema["x-concreteTypes"]:
                ref_link = ref_dict['$ref']
                types += [link.split("/")[-1] for link in self.list_concrete_types_recursive(ref_link)]
        return types

    def list_concrete_types_recursive(self, reference):
        references = []
        schema = self.lookup(reference)
        if "x-concreteTypes" not in schema:
            references.append(reference)
        else:
            for ref_dict in schema["x-concreteTypes"]:
                references += self.list_concrete_types_recursive(ref_dict['$ref'])
        return references

    def handle_oneof(self, data, obj_type=None):
        '''
        Returns full reference to object if obj_type is present inside oneOf block
        '''
        list_typedata = data['oneOf']
        response_ref = None
        for type_dict in list_typedata:
            if '$ref' in type_dict and type_dict['$ref'].split('/')[-1] == obj_type:
                return type_dict['$ref']


class _OpenAPIv2Spec(_OpenAPIBaseSpec):
    @property
    def base_path(self):
        return self.raw_spec["basePath"]

    def get_response_ref(self, route, http_method):
        route_data = self.raw_spec['paths'][route]
        responses = route_data[http_method]['responses']
        response_code = success_codes[http_method]
        if response_code in responses:
            response_200 = responses[response_code]
            if 'schema' in response_200:
                schema = response_200['schema']
                if '$ref' in schema:
                    response_ref = schema['$ref']
                    return response_ref

    def get_body_type_params(self, route, http_method):
        route_data = self.raw_spec['paths'][route][http_method]
        data = route_data.get('parameters', [])
        if data:
            return dict(
                schema = data[0].get('schema'),
                required = data[0].get('required'),
                description = data[0].get('description'),
                name = [data[0].get('name'),]
            )
        return {}

    def get_path_type_params(self, route):
        route_data = self.raw_spec['paths'][route]
        params = [param for param in route_data.get('parameters', '')]
        return params

    def returns_iterable(self, route, http_method):
        result = False
        responses = self.raw_spec['paths'][route][http_method]['responses']
        response_code = success_codes[http_method]
        if response_code in responses:
            response_200 = responses.get(response_code)
            if 'schema' in response_200:
                schema = response_200['schema']
                if '$ref' in schema:
                    object_key = schema['$ref'].split('/')[-1]
                    object_descr = self.raw_spec['definitions'][object_key]
                    object_properties = object_descr['properties']
                    data_structure = object_properties['data']
                    result = 'array' == data_structure.get('type')
        return result

    def get_default_options(self, route, http_method):
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
                            f_key.get("properties", {}).get("id", {}).get("type") in ("integer", "string"):
                                    column_names.append("%s.id" % k)
        return column_names

    def filter_json_object(self, data, route, http_method, filter_createonly=False,
                            schema=None, reference=None):
        """
        Removes immutable parts from JSON object
        before sending it in POST or PATCH.
        """

        filtered = {}

        # load `schema`
        if schema is None:
            param = self.get_body_type_params(route, http_method)
            if 'schema' in param:
                schema = param['schema']
                if '$ref' in schema:
                    reference = schema['$ref']
                    schema = self.lookup(schema['$ref'])

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


class _OpenAPIv3Spec(_OpenAPIBaseSpec):
    @property
    def base_path(self):
        servers = self.raw_spec["servers"]
        default_server = servers[0]
        result = default_server["url"]
        path = parse.urlsplit(result).path
        return path[:-1]

    def get_response_ref(self, route, http_method):
        responses = self.raw_spec['paths'][route][http_method]['responses']
        response_200 = responses.get(success_codes[http_method])
        if '$ref' in response_200:
            response_200 = self.lookup(response_200['$ref'])
        result = response_200['content']['application/json']['schema']['$ref']
        return result

    def get_body_type_params(self, route, http_method):

        def list_references_oneOf(data):
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
            raw_block = self.lookup(request_body.get("$ref")) if "$ref" in request_body else request_body
            param["schema"] = raw_block["content"]['application/json']["schema"]
            param["required"] = raw_block.get("required")
            param["description"] = raw_block.get("description")
            schema = param["schema"]

            if '$ref' in schema:
                param["name"] = [raw_block.get("name", schema['$ref'].split('/')[-1]), ]
            elif 'oneOf' in schema:
                param["name"] = [ref.split('/')[-1] for ref in list_references_oneOf(schema)]

            return param
        return {}

    def get_path_type_params(self, route):
        route_data = self.raw_spec['paths'][route]
        params = []
        for param in route_data.get('parameters', ''):
            if '$ref' in param:
                obj = self.lookup(param['$ref'])
                params.append(obj)
            else:
                params.append(param)
        return params

    def returns_iterable(self, route, http_method):
        responses = self.raw_spec['paths'][route]['get']['responses']
        if success_codes[http_method] in responses:
            response_200 = responses.get(success_codes[http_method])
            if "$ref" in response_200:
                response_200 = self.lookup(response_200['$ref'])
            if 'schema' in response_200["content"]["application/json"]:
                schema = response_200["content"]["application/json"]["schema"]
                if '$ref' in schema:
                    schema = self.lookup(schema["$ref"])
                object_properties = schema['properties']
                data_structure = object_properties['data']
                result = 'array' == data_structure.get('type')
                return result
        return False

    def get_default_options(self, route, http_method):
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
        data = self.result_descr(route, http_method)['properties']['data']
        if 'items' in data:
            items = data['items']
            if 'oneOf' in items:
                response_ref = self.handle_oneof(items, obj_type)
                if not response_ref:
                    return []
            else:
                response_ref = items['$ref']
        elif '$ref' in data:
            response_ref = data['$ref']
        elif 'oneOf' in data:
            response_ref = self.handle_oneof(data, obj_type)
        response_descr = self.lookup(response_ref)
        if 'allOf' in response_descr:
            properties = self.merge_all(response_descr).get('properties', {})
        else:
            properties = response_descr.get('properties', {})

        column_names = []
        for k, v in properties.items():
            if '$ref' not in v:
                column_names.append(k)
            else:  # ST-226
                f_key = self.lookup(v['$ref'])
                if "properties" in f_key:
                    if len(f_key["properties"]) == 1:
                        if "id" in f_key["properties"]:
                            if "type" in f_key["properties"]["id"]:
                                if f_key["properties"]["id"]["type"] in ("integer", "string"):
                                    column_names.append("%s.id" % k)
        return column_names

    def merge_all(self, data):
        return utils.merge_all(data, self.raw_spec)

    def filter_json_object(self, data, route, http_method, filter_createonly=False,
                            schema=None, reference=None):
        """
        Removes immutable parts from JSON object
        before sending it in POST or PATCH.
        """
        filtered = {}

        # load `schema`
        if schema is None:
            param = self.get_body_type_params(route, http_method)
            if 'schema' in param:
                schema = param['schema']
                if '$ref' in schema:
                    reference = schema['$ref']
                    schema = self.lookup(schema['$ref'])

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
                schema = self.merge_all(schema)

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
                        sub_schema = self.merge_all(sub_schema)

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


class PolledAction(SimplifiedAction):

    def _wait_for_status(self, poll_dict, action_obj, states_to_wait_for, timeout=1, hide_output=True, **kwargs):
        '''

        :param poll_dict: e.g. {'serverId': b039d8d9-26c2-439d-9b2b-9d7b761b417c}
        :param action_obj: instance of class Action
        :param states_to_wait_for: list of states to wait for, e.g. ('running', 'failed')
        :param timeout: timeout in secons between attempts
        :param hide_output: when False prints full polling status
        :param kwargs: the same dict that run() method accepts
        :returns last status, e.g. 'running'
        '''
        status = ''
        with utils._spinner():
            while status not in states_to_wait_for:
                run_args = {"hide_output": hide_output, "envId": kwargs.get('envId')}
                run_args.update(poll_dict)
                data = action_obj.run(**run_args)
                data_json = json.loads(data)
                status = self._get_operation_status(data_json)
                time.sleep(timeout)
        return status

    def _get_operation_status(self, data_json):
        return data_json["data"]["status"]

