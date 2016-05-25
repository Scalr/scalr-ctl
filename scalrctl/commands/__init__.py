__author__ = 'Dmitriy Korsakov'

import os
import re
import json
import traceback

from scalrctl import click
from scalrctl import defaults
from scalrctl import settings
from scalrctl import request
from scalrctl.view import build_table, build_tree



class BaseAction(object):

    epilog = None

    def __init__(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        pass

    def get_description(self):
        return ""

    def modify_options(self, options):
        return options

    def get_options(self):
        return []

    def validate(self):
        pass


class Action(BaseAction):

    raw_spec = None
    prompt_for = None  # Optional. Some values like GCE imageId cannot be passed through command lines
    mutable_body_parts = None  # Temporary. Object definitions in YAML spec are not always correct
    object_reference = None # optional, e.g. '#/definitions/GlobalVariable'

    _table_columns = None

    def __init__(self, name, route, http_method, api_level, *args, **kwargs):
        self.name = name
        self.route = route
        self.http_method = http_method
        self.api_level = api_level

        self._table_columns = []

        self._init()

    def _init(self):
        path = os.path.join(defaults.CONFIG_DIRECTORY, "%s.json" % self.api_level)
        self.raw_spec = json.load(open(path, "r"))

        if not self.epilog and self.http_method.upper() == "POST":
            self.epilog = "Example: scalr-ctl %s < %s.json" % (self.name, self.name)

    def validate(self):
        if self.route and self.api_level and os.path.exists(defaults.ROUTES_PATH):
            available_api_routes = json.load(open(defaults.ROUTES_PATH))
            assert self.api_level in available_api_routes and self.route in available_api_routes[self.api_level], \
                self.name

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        raw_columns = kwargs.pop("columns", False)
        if raw_columns:
            self._table_columns = raw_columns.split(",")

        raw_filters = kwargs.pop("filters", None)
        if raw_filters:
            for pair in raw_filters.split(","):
                kv = pair.split("=")
                if 2 == len(kv):
                    kwargs[kv[0]] = kv[1]

        if "debug" in kwargs:
            settings.debug_mode = kwargs.pop("debug")
        if "transformation" in kwargs:
            settings.view = kwargs.pop("transformation")
        if "nocolor" in kwargs:
            settings.colored_output = not kwargs.pop("nocolor")
        import_data = kwargs.pop("import-data", None)

        if self.http_method.upper() in ("PATCH", "POST"):
            # prompting for body and then validating it
            for param in self.get_body_type_params():
                name = param["name"]
                text = ''
                if self.http_method.upper() == "PATCH":
                    if import_data and name in import_data:
                        import_data[name] = self._filter_json_object(import_data[name], filter_createonly=True)
                    else:
                        try:
                            get_object = Action(
                                name="get",
                                route=self.route,
                                http_method="get",
                                api_level=self.api_level
                            )  # XXX: can be custom class
                            raw_text = get_object.run(*args, **kwargs)
                            if settings.debug_mode:
                                click.echo(raw_text)

                            json_text = json.loads(raw_text)
                            filtered = self._filter_json_object(json_text['data'], filter_createonly=True)
                            text = json.dumps(filtered)
                        except (Exception, BaseException) as e:
                            if settings.debug_mode:
                                click.echo(traceback.format_exc())
                            else:
                                click.echo(e)

                if import_data and name in import_data:
                    user_object = import_data[name]

                else:
                    if self.http_method.upper() == "PATCH":
                        raw = click.edit(text)
                    else:
                        raw = click.get_text_stream("stdin").read()
                    try:
                        user_object = json.loads(raw)
                    except (Exception, BaseException) as e:
                        if settings.debug_mode:
                            raise
                        raise click.ClickException(str(e))

                valid_object = self._filter_json_object(user_object)
                valid_object_str = json.dumps(valid_object)
                kwargs[name] = valid_object_str

        return args, kwargs

    def post(self, response):
        """
        after request is made
        """
        return response

    def run(self, *args, **kwargs):
        """
        callback for click subcommand
        """
        # print "run %s @ %s with arguments:" % (self.http_method, self.route), args, kwargs
        hide_output = kwargs.pop("hide_output", False) # [ST-88]

        args, kwargs = self.pre(*args, **kwargs)

        uri = self._request_template
        payload = {}
        data = None

        if settings.envId and '{envId}' in uri and ('envId' not in kwargs or not kwargs['envId']):
            kwargs['envId'] = settings.envId  # XXX

        if kwargs:
            uri = self._request_template.format(**kwargs)

            for key, value in kwargs.items():
                t = "{%s}" % key
                # filtering in-body and empty params
                if value and t not in self._request_template:
                    if self.http_method.upper() in ("GET", "DELETE"):
                        payload[key] = value
                    elif self.http_method.upper() in ("POST", "PATCH"):
                        data = value  # XXX

        raw_response = request.request(self.http_method, uri, payload, data)
        response = self.post(raw_response)

        if settings.view == "raw" and not hide_output:
            click.echo(raw_response)

        if raw_response:

            try:
                response_json = json.loads(response)
            except ValueError as e:
                if settings.debug_mode:
                    raise
                raise click.ClickException(str(e))

            if "errors" in response_json and response_json["errors"]:
                raise click.ClickException(response_json["errors"][0]['message'])

            data = response_json["data"]
            text = json.dumps(data)

            if settings.debug_mode and not hide_output:
                click.echo(response_json["meta"])

            if settings.view == "tree" and not hide_output:
                click.echo(build_tree(text))

            elif settings.view == "table":
                columns = self._table_columns or self._get_column_names()
                rows = []
                for block in data:
                    row = []
                    for name in columns:
                        for item in block:
                            if name.lower() == item.lower():
                                row.append(block[item])
                                break
                        else:
                            raise click.ClickException("Cannot apply filter. No such column: %s" % name)
                    if row:
                        rows.append(row)

                pagination = response_json.get("pagination", None)
                if pagination:
                    pagenum_last, current_pagenum = 1, 1
                    url_last = pagination.get('last', None)
                    if url_last:
                        number = re.search("pageNum=(\d*)", url_last)
                        pagenum_last = number.group(1) if number else 1

                    url_next = pagination.get('next', None)
                    if url_next:
                        num = re.search("pageNum=(\d*)", url_next)
                        pagenum_next = num.group(1) if num else 1
                        current_pagenum = int(pagenum_next) - 1

                if not hide_output:
                    click.echo(build_table(columns, rows, "Page: %s of %s" % (current_pagenum, pagenum_last)))  # XXX

        return response

    def get_description(self):
        return self.raw_spec["paths"][self.route][self.http_method]["description"]

    def get_options(self):
        return self._get_default_options() + self._get_custom_options()

    def modify_options(self, options):
        """
        this is the place where command line options can be fixed
        after they are loaded from yaml spec
        """
        for option in options:
            if self.prompt_for and option.name in self.prompt_for:
                option.prompt = option.name

            if option.name == "envId" and settings.envId:
                option.required = False

        return options

    def _get_default_options(self):
        options = []
        for param in self._get_raw_params():
            option = click.Option(
                ("--%s" % param['name'], param['name']),
                required=param['required'],
                help=param["description"]
            )
            options.append(option)
        return options

    def _get_custom_options(self):
        options = []
        debug = click.Option(('--debug/--no-debug', 'debug'), default=False, help="Print debug messages")
        options.append(debug)

        if self.http_method.upper() == 'GET' and self.name != "export":  # [ST-88]
            raw = click.Option(
                ('--raw', 'transformation'),
                is_flag=True,
                flag_value='raw',
                default=False,
                help="Print raw response"
            )
            tree = click.Option(
                ('--tree', 'transformation'),
                is_flag=True,
                flag_value='tree',
                default=True,
                help="Print response as a colored tree"
            )
            nocolor = click.Option(('--nocolor', 'nocolor'), is_flag=True, default=False, help="Use colors")
            options += [raw, tree, nocolor]

            if self.name not in ("get", "retrieve"):  # [ST-54] [ST-102]
                table = click.Option(
                    ('--table', 'transformation'),
                    is_flag=True,
                    flag_value='table',
                    default=False,
                    help="Print response as a colored table"
                )
                options.append(table)

            if self._returns_iterable():
                maxrez = click.Option(
                    ("--maxresults", "maxResults"),
                    type=int,
                    required=False,
                    help="Maximum number of records. Example: --maxresults=2"
                )
                options.append(maxrez)

                pagenum = click.Option(
                    ("--pagenumber", "pageNum"),
                    type=int,
                    required=False,
                    help="Current page number. Example: --pagenumber=3"
                )
                options.append(pagenum)

                filter_help = "Apply filters. Example: type=ebs,size=8. "
                filters = self._get_available_filters()
                if filters:
                    filters = sorted(filters)
                    filter_help += "Available filters: %s." % ", ".join(filters)
                    filters = click.Option(("--filters", "filters"), required=False, help=filter_help)
                    options.append(filters)

                columns_help = "Filter columns in table view [--table required]. Example: NAME,SIZE,SCOPE. "
                available_columns = self._get_column_names()
                columns_help += "Available columns: %s." % ", ".join(available_columns)
                columns = click.Option(("--columns", "columns"), required=False, help=columns_help)
                options.append(columns)

        return options

    def get_body_type_params(self):
        params = []
        m = self.raw_spec["paths"][self.route][self.http_method]
        if "parameters" in m:
            for parameter in m['parameters']:
                params.append(parameter)
        return params

    def _get_path_type_params(self):
        params = []
        d = self.raw_spec["paths"][self.route]
        if "parameters" in d:
            for parameter in d['parameters']:
                params.append(parameter)
        return params

    def _get_raw_params(self):
        result = self._get_path_type_params()
        if self.http_method.upper() in ("GET", "DELETE"):
            body_params = self.get_body_type_params()
            result += body_params
        return result

    def _returns_iterable(self):
        responses = self.raw_spec["paths"][self.route]["get"]['responses']
        if '200' in responses:
            ok200 = responses['200']
            if 'schema' in ok200:
                schema = ok200['schema']
                if '$ref' in schema:
                    reference = schema['$ref']
                    object_key = reference.split("/")[-1]
                    object_descr = self.raw_spec["definitions"][object_key]
                    object_properties = object_descr["properties"]
                    data_structure = object_properties["data"]
                    if "type" in data_structure:
                        response_type = data_structure["type"]
                        if "array" == response_type:
                            return True
        return False

    def _get_available_filters(self):
        if self._returns_iterable():
            response_ref = self._result_descr["properties"]["data"]["items"]["$ref"]
            response_descr = self._lookup(response_ref)
            if "x-filterable" in response_descr:
                filters = response_descr["x-filterable"]
                return filters
        return []

    def _get_column_names(self):
        fields = []
        data = self._result_descr["properties"]["data"]
        response_ref = data["items"]["$ref"]
        response_descr = self._lookup(response_ref)
        for k, v in response_descr["properties"].items():
            if "$ref" not in v:
                fields.append(k)
        return sorted(fields)

    def _lookup(self, refstr):
        """
        Returns document section
        Example: #/definitions/Image returns Image defenition section
        """
        if refstr.startswith("#"):
            paths = refstr.split("/")[1:]
            result = self.raw_spec
            for path in paths:
                if path not in result:
                    return
                result = result[path]
            return result

    @property
    def _result_descr(self):
        responses = self.raw_spec["paths"][self.route][self.http_method]['responses']
        if '200' in responses:
            ok200 = responses['200']
            if 'schema' in ok200:
                schema = ok200['schema']
                if '$ref' in schema:
                    reference = schema['$ref']
                    return self._lookup(reference)

    def _filter_json_object(self, obj, filter_createonly=False):
        """
        removes immutable parts from JSON object before sending it in POST or PATCH
        """
        # XXX: make it recursive
        result = {}
        mutable_parts = self.mutable_body_parts or self._list_mutable_body_parts()
        for name, value in obj.items():
            if filter_createonly and name in self._list_createonly_properties():
                continue
            elif name in mutable_parts:
                result[name] = obj[name]
        return result

    def _list_mutable_body_parts(self):
        """
        finds object in yaml spec and determines it's mutable fields
        to filter user JSON
        """
        mutable = []
        reference_path = None

        if not self.object_reference:
            for param in self.get_body_type_params():
                name = param["name"]  # e.g. image
                if "schema" in param:
                    if '$ref' in param["schema"]:
                        reference_path = param["schema"]['$ref']  # e.g. #/definitions/Image
                    elif "properties" in param["schema"]:  # ST-98, got object instead of $ref
                        for _property, description in param["schema"]["properties"].items():
                            if 'readOnly' not in description or not description['readOnly']:
                                mutable.append(_property)

                elif 'readOnly' not in param:
                    # e.g. POST /{envId}/farms/{farmId}/actions/terminate/
                    mutable.append(name)

        else:
            # XXX: Temporary code, see GlobalVariableDetailEnvelope or "role-global-variables update"
            reference_path = self.object_reference

        if reference_path:
            parts = reference_path.split("/")
            obj = self.raw_spec[parts[1]][parts[2]]
            object_properties = obj["properties"]
            for _property, description in object_properties.items():
                if 'readOnly' not in description or not description['readOnly']:
                        mutable.append(_property)
        return mutable

    def _list_createonly_properties(self):
        """
        Some properties (mostly IDs) cannot be marked as read-only because they are
        passed in PUT-methods (but still must be filtered in UPDATE-methods)
        """
        result = []
        properties = self._result_descr['properties']
        data = properties['data']
        if 'items' in data:
            path = data['items']['$ref']
        else:
            path = data['$ref']
        obj = self._lookup(path)
        if 'x-createOnly' in obj:
            result = obj['x-createOnly']
        return result

    @property
    def _request_template(self):
        basepath_uri = self.raw_spec["basePath"]
        return "%s%s" % (basepath_uri, self.route)