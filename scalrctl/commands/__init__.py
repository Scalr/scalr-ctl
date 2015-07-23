__author__ = 'Dmitriy Korsakov'

import click

import re
import json
import traceback
from collections import defaultdict

from scalrctl import settings
from scalrctl import request
from scalrctl import spec
from scalrctl.view import build_table, build_tree


enabled = False


class SubCommandMeta(type):

    def __new__(mcs, name, parents, dct):
        route = dct.get("route")
        c = super(SubCommandMeta, mcs).__new__(mcs, name, parents, dct)
        if name!="SubCommand" and route:
            SubCommand._siblings[route].append(c)
        return c


class SubCommand(object):
    __metaclass__ = SubCommandMeta
    _siblings = defaultdict(list)
    name = None
    route = None
    method = None
    enabled = False
    _table_columns = None

    mutable_body_parts = None # temporary, object definitions in YAML spec are not always correct
    object_reference = None # optional, e.g. '#/definitions/GlobalVariable'
    prompt_for = None #optional, Some values like GCE imageId cannot be passed through command line

    def __init__(self):
        self._table_columns = []

    @property
    def spc(self):
        return spec.Spec(spec.get_raw_spec(), self.route, self.method)

    def get_siblings(self):
        return SubCommand._siblings.get(self.route)

    @property
    def _basepath_uri(self):
        return spec.get_raw_spec()["basePath"]

    @property
    def _request_template(self):
        return "%s%s" % (self._basepath_uri, self.route)

    def modify_options(self, options):
        """
        this is the place where command line options can be fixed
        after they are loaded from yaml spec
        """
        #print "In SubCommand modifier"
        for option in options:
            if self.prompt_for and option.name in self.prompt_for:
                option.prompt = option.name

            if option.name == "envId" and settings.envId:
                option.required = False

        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        raw_columns = kwargs.pop("columns", False)
        if raw_columns:
            self._table_columns = raw_columns.split(",")

        settings.debug_mode = kwargs.pop("debug", False)
        settings.view = kwargs.pop("transformation", "tree")
        settings.colored_output = not kwargs.pop("nocolor", False)

        raw_filters = kwargs.pop("filters", None)

        if raw_filters:
            for pair in raw_filters.split(","):
                kv = pair.split("=")
                if 2==len(kv):
                    kwargs[kv[0]]=kv[1]


        stdin = kwargs.pop("stdin", False)

        if self.method.upper() in ("PATCH", "POST"):
            #prompting for body and then validating it
            for param in self._post_params():
                name = param["name"]

                if stdin:
                    raw = click.termui.prompt("Input %s in JSON format" % name)
                else:
                    text = ''
                    if self.method.upper() == "PATCH":
                        try:
                            for cls in self.get_siblings():
                                if cls.method.upper() == "GET":
                                    rawtext = cls().run(*args, **kwargs)

                                    if settings.debug_mode:
                                        click.echo(rawtext)

                                    json_text = json.loads(rawtext)
                                    filtered = self._filter_json_object(json_text['data'], filter_createonly=True)
                                    text = json.dumps(filtered)
                        except (Exception, BaseException), e:
                            if settings.debug_mode:
                                click.echo(traceback.format_exc())
                            else:
                                click.echo(e)
                    raw = click.edit(text)

                try:
                    user_object = json.loads(raw)
                except (Exception, BaseException), e:
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
                    if self.method.upper() in ("GET", "DELETE"):
                        payload[key] = value
                    elif self.method.upper() in ("POST", "PATCH"):
                        data = value  #XXX

        raw_response = request.request(self.method, uri, payload, data)
        response = self.post(raw_response)

        if settings.view == "raw":
            click.echo(raw_response)

        if raw_response:

            response_json = json.loads(response)

            if "errors" in response_json and response_json["errors"]:
                raise click.ClickException(response_json["errors"][0]['message'])

            data = response_json["data"]
            text = json.dumps(data)

            if settings.debug_mode:
                click.echo(response_json["meta"])

            if settings.view == "tree":
                click.echo(build_tree(text))

            elif settings.view == "table":
                columns = self._table_columns or self.spc.get_column_names()
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



                click.echo(build_table(columns, rows, "Page: %s of %s" % (current_pagenum, pagenum_last))) #XXX

        return response


    def _list_mutable_body_parts(self):
        """
        finds object in yaml spec and determines it's mutable fields
        to filter user JSON
        XXX: Move to Spec (?) after TODO#3
        """
        mutable = []
        reference_path = None

        ### spcobj = spec.Spec(settings.spec, self.route, self.method)
        ### print "descr:", spcobj._result_descr

        if not self.object_reference:
            for param in spec.get_raw_spec()["paths"][self.route][self.method]["parameters"]:
                name = param["name"] # image
                if "schema" in param:
                    reference_path = param["schema"]['$ref'] # #/definitions/Image
                elif 'readOnly' not in param:
                    # e.g. POST /{envId}/farms/{farmId}/actions/terminate/
                    mutable.append(name)
        else:
            #XXX: Temporary code, see GlobalVariableDetailEnvelope or "role-global-variables update"
            reference_path = self.object_reference
        #print "reference_path", reference_path
        
        if reference_path:
            parts = reference_path.split("/")
            object =  spec.get_raw_spec()[parts[1]][parts[2]]
            object_properties = object["properties"]
            for property, descr in object_properties.items():
                if 'readOnly' not in descr or not descr['readOnly']:
                        mutable.append(property)
        return mutable

    def _list_createonly_properties(self):
        """
        Some properties (mostly IDs) cannot be marked as read-only because they are
        passed in PUT-methods (but still must be filtered in UPDATE-methods)
        """
        result = []
        properties = self.spc._result_descr['properties']
        data = properties['data']
        if 'items' in data:
            path = data['items']['$ref']
        else:
            path = data['$ref']
        obj = self.spc.lookup(path)
        if 'x-createOnly' in obj:
            result = obj['x-createOnly']
        return result

    def _filter_json_object(self, obj, filter_createonly=False):
        """
        removes immutable parts from JSON object before sending it in POST or PATCH
        """
        #XXX: make it recursive
        result = {}
        mutable_parts = self.mutable_body_parts or self._list_mutable_body_parts()
        for name, value in obj.items():
            if filter_createonly and name in self._list_createonly_properties():
                continue
            elif name in mutable_parts:
                result[name] = obj[name]
        return result

    def _post_params(self):
        """
        Determines list of body params
        e.g. 'image' JSON object for 'change-attributes' command
        """
        params = []
        m = spec.get_raw_spec()["paths"][self.route][self.method]
        if "parameters" in m:
            for parameter in m['parameters']:
                params.append(parameter)
        return params