# -*- coding: utf-8 -*-
import json
import re
import os

import dicttoxml

from scalrctl import click, request, settings, utils, view, examples, defaults

__author__ = 'Dmitriy Korsakov'


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
    _table_columns = None

    def __init__(self, name, route, http_method, api_level, *args, **kwargs):
        self.name = name
        self.route = route
        self.http_method = http_method
        self.api_level = api_level
        self._table_columns = []

        self._init()

    def _init(self):
        self.raw_spec = utils.read_spec(self.api_level, ext='json')

        if not self.epilog and self.http_method.upper() == 'POST':
            msg = "Example: scalr-ctl {level} {name} < {name}.json"
            self.epilog = msg.format(
                level=self.api_level if self.api_level != 'user' else '',
                name=self.name
            )

    def validate(self):
        """
        Validate routes for current API scope.
        """
        if self.route and self.api_level:
            spec_path = os.path.join(defaults.CONFIG_DIRECTORY,
                                     '{}.json'.format(self.api_level))
            api_routes = json.load(open(spec_path, 'r'))['paths'].keys()
            assert api_routes and self.route in api_routes, self.name

    def _check_arguments(self, **kwargs):
        route_data = self.raw_spec['paths'][self.route]
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

        if kwargs.pop('dryrun', False):
            self.dry_run = True

        if kwargs.pop('debug', None):
            settings.debug_mode = True

        if kwargs.pop('nocolor', None):
            settings.colored_output = False

        if kwargs.get('transformation'):
            settings.view = kwargs.pop('transformation')

        return kwargs

    def _get_object(self, *args, **kwargs):
        try:
            obj = self.__class__(name='get', route=self.route,
                                 http_method='get', api_level=self.api_level)
            raw_text = obj.run(*args, **kwargs)
            utils.debug(raw_text)
            if raw_text is None:
                return {}
            json_text = json.loads(raw_text)
            filtered = self._filter_json_object(json_text['data'],
                                                filter_createonly=True)
            return json.dumps(filtered, indent=2)
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

    def _format_response(self, response, hidden=False, **kwargs):
        text = None

        if response:
            try:
                response_json = json.loads(response)
            except ValueError:
                utils.debug("Server response: {}".format(str(response)))
                utils.reraise("Invalid server response")

            if response_json.get('errors'):
                msg = response_json['errors'][0]['message']
                raise click.ClickException(msg)

            if not hidden:
                utils.debug(response_json.get('meta'))

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
                columns = self._table_columns or self._get_column_names()
                rows, current_page, last_page = view.calc_table(response_json,
                                                                columns)
                pre = "Page: {} of {}".format(current_page, last_page)
                click.echo(view.build_table(columns, rows, pre=pre))  # XXX
        elif self.http_method.upper() == 'DELETE':
            deleted_id = ''
            for param, value in kwargs.items():
                if 'Id' in param and param != 'envId':
                    deleted_id = value
                    break
            text = "Deleted {}".format(deleted_id)
        return text

    def _get_default_options(self):
        options = []
        for param in self._get_raw_params():
            option = click.Option(('--{}'.format(param['name']),
                                  param['name']), required=param['required'],
                                  help=param['description'])
            options.append(option)
        return options

    def _get_custom_options(self):
        options = []

        if self.http_method.upper() == 'POST':
            stdin = click.Option(('--stdin', 'stdin'),
                                       is_flag=True, required=False,
                                       help="Read JSON data from standart console input instead of "
                                            "editing it in the default "
                                            "console text editor.")
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
            if self._returns_iterable():
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

                columns_help = ("Filter columns in table view "
                                "[--table required]. Example: NAME,SIZE,"
                                "SCOPE. Available columns: {}."
                                ).format(', '.join(self._get_column_names()))
                columns = click.Option(('--columns', 'columns'),
                                       required=False, help=columns_help)
                options.append(columns)

            raw = click.Option(('--raw', 'transformation'), is_flag=True,
                               flag_value='raw', default=False, hidden=True,
                               help="Print raw response")
            json_ = click.Option(('--json', 'transformation'), is_flag=True,
                                 flag_value='raw', default=False,
                                 help="Print raw response")
            xml = click.Option(('--xml', 'transformation'), is_flag=True,
                               flag_value='xml', default=False,
                               help="Print response as a XML")
            tree = click.Option(('--tree', 'transformation'), is_flag=True,
                                flag_value='tree', default=False,
                                help="Print response as a colored tree")
            nocolor = click.Option(('--nocolor', 'nocolor'), is_flag=True,
                                   default=False, help="Use colors")
            options += [raw, tree, nocolor, json_, xml]

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
        responses = self.raw_spec['paths'][self.route]['get']['responses']
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
        if self._returns_iterable():
            data = self._result_descr['properties']['data']
            response_ref = data['items']['$ref']
            response_descr = self._lookup(response_ref)
            if 'x-filterable' in response_descr:
                return response_descr['x-filterable']
        return []

    def _get_column_names(self):
        data = self._result_descr['properties']['data']
        # XXX: Inconsistency in swagger spec.
        # See RoleDetailsResponse vs RoleCategoryListResponse
        response_ref = data['items']['$ref'] \
            if 'items' in data else data['$ref']
        response_descr = self._lookup(response_ref)
        properties = response_descr['properties']
        return sorted(k for k, v in properties.items() if '$ref' not in v)

    def _lookup(self, response_ref):
        """
        Returns document section
        Example: #/definitions/Image returns Image defenition section.
        """
        if response_ref.startswith('#'):
            paths = response_ref.split('/')[1:]
            result = self.raw_spec
            for path in paths:
                if path not in result:
                    return
                result = result[path]
            return result

    @property
    def _result_descr(self):
        route_data = self.raw_spec['paths'][self.route]
        responses = route_data[self.http_method]['responses']
        if '200' in responses:
            response_200 = responses['200']
            if 'schema' in response_200:
                schema = response_200['schema']
                if '$ref' in schema:
                    response_ref = schema['$ref']
                    return self._lookup(response_ref)

    def _filter_json_object(self, obj, filter_createonly=False):
        """
        Removes immutable parts from JSON object
        before sending it in POST or PATCH.
        """
        # XXX: make it recursive
        result = {}
        createonly_properties = self._list_createonly_properties()
        mutable_parts = self.mutable_body_parts or \
            self._list_mutable_body_parts()

        for name, value in obj.items():
            if filter_createonly and name in createonly_properties:
                continue
            elif name in mutable_parts:
                result[name] = obj[name]

        return result

    def _list_mutable_body_parts(self):
        """
        Finds object in yaml spec and determines it's mutable fields
        to filter user JSON.
        """
        # TODO: remove this method
        mutable = []
        reference_path = None

        if not self.object_reference:
            for param in self._get_body_type_params():
                if 'schema' in param:
                    if '$ref' in param['schema']:
                        reference_path = param['schema']['$ref']
                    elif 'properties' in param['schema']:
                        # ST-98, got object instead of $ref
                        subparams = param['schema']['properties']
                        for subparam, description in subparams.items():
                            if not description.get('readOnly'):
                                mutable.append(subparam)
                elif 'readOnly' not in param:
                    # e.g. POST /{envId}/farms/{farmId}/actions/terminate/
                    mutable.append(param['name'])
        else:
            # XXX: Temporary code, see GlobalVariableDetailEnvelope
            # or "role-global-variables update"
            reference_path = self.object_reference

        if reference_path:
            parts = reference_path.strip('#/').split('/')
            params = self.raw_spec[parts[0]][parts[1]]['properties']
            for param, description in params.items():
                if not description.get('readOnly'):
                    mutable.append(param)
        return mutable

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
            obj = self._lookup(path)
            return obj['x-createOnly'] if 'x-createOnly' in obj else []

    @property
    def _request_template(self):
        basepath_uri = self.raw_spec['basePath']
        return '{}{}'.format(basepath_uri, self.route)

    def pre(self, *args, **kwargs):
        """
        Before request is made.
        """
        kwargs = self._apply_arguments(**kwargs)
        self._check_arguments(**kwargs)

        import_data = kwargs.pop('import-data', {})
        #interactive = kwargs.pop('interactive', None)
        stdin = kwargs.pop('stdin', None)
        http_method = self.http_method.upper()

        if http_method not in ('PATCH', 'POST'):
            return args, kwargs

        # prompting for body and then validating it
        for param_name in (p['name'] for p in self._get_body_type_params()):
            try:
                if param_name in import_data:
                    json_object = self._filter_json_object(
                        import_data[param_name],
                        filter_createonly=True
                    ) if http_method == 'PATCH' else import_data[param_name]
                else:
                    if http_method == 'PATCH':
                        json_object = self._edit_object(*args, **kwargs)
                    elif http_method == 'POST' and not stdin:
                        json_object = self._edit_example()
                    else:
                        json_object = self._read_object()

                json_object = self._filter_json_object(json_object)
                kwargs[param_name] = json_object
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

        if kwargs:
            # filtering in-body and empty params
            uri = self._request_template.format(**kwargs)
            for key, value in kwargs.items():
                param = '{{{}}}'.format(key)
                if value and (param not in self._request_template):
                    body_params = self._get_body_type_params()
                    if self.http_method.upper() in ('GET', 'DELETE'):
                        payload[key] = value
                    elif body_params and key == body_params[0]['name']:
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
        route_data = self.raw_spec['paths'][self.route]
        return route_data[self.http_method]['description']

    def modify_options(self, options):
        """
        This is the place where command line options can be fixed
        after they are loaded from yaml spec.
        """
        for option in options:
            if self.prompt_for and option.name in self.prompt_for:
                option.prompt = option.name
            if option.name == 'envId' and settings.envId:
                option.required = False
        return options

    def get_options(self):
        """
        Returns action options.
        """
        return self._get_default_options() + self._get_custom_options()

    def validate(self):
        """
        Validate routes for current API scope.
        """
        if self.route and self.api_level:
            spec_path = os.path.join(defaults.CONFIG_DIRECTORY,
                                     '{}.json'.format(self.api_level))
            api_routes = json.load(open(spec_path, 'r'))['paths'].keys()
            assert api_routes and self.route in api_routes, self.name
