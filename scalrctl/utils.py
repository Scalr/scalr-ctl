"""
Module that provides utils for client.
"""
# -*- coding: utf-8 -*-
import itertools
import typing  # pylint: disable=unused-import
import os
import sys
import json
import time
import threading
import traceback
import yaml

from scalrctl import click, defaults, settings
# pylint: disable=unused-import
from scalrctl.commands import openapi


SUCCESS_CODES = {
    'get': '200',
    'post': '201',
    'delete': '204',
    'patch': '200',
}


def get_col_name_from_prop(properties, raw_spec):
    """
    Compound column names from properties.
    """
    column_names = []
    for k, v in properties.items():
        if '$ref' not in v:
            column_names.append(k)
        else:  # ST-226
            f_key = lookup(v['$ref'], raw_spec)
            if "properties" in f_key and len(f_key["properties"]) == 1 and \
               f_key.get("properties", {}).get("id", {}).get("type") in \
               ("integer", "string"):
                column_names.append("%s.id" % k)
    return column_names


def get_column_names_v2(data, route, http_method, raw_spec, obj_type=None):
    # type: (dict, str, str, dict, str) -> typing.List[str]
    """
    Compound column names into list for OpenAPI2
    """
    response_ref = data['items']['$ref'] \
        if 'items' in data else data['$ref']
    response_descr = lookup(response_ref, raw_spec)
    properties = response_descr['properties']
    column_names = get_col_name_from_prop(properties, raw_spec)

    return column_names


def get_column_names_v3(data, route, http_method, raw_spec, obj_type=None):
    # type: (dict, str, str, dict, str) -> typing.List[str]
    """
    Compound column names into list for OpenAPI3
    """
    if 'items' in data:
        items = data['items']
        if 'oneOf' in items:
            response_ref = handle_oneof(items, obj_type)
            if not response_ref:
                return []
        else:
            response_ref = items['$ref']
    elif '$ref' in data:
        response_ref = data['$ref']
    elif 'oneOf' in data:
        response_ref = handle_oneof(data, obj_type)
    response_descr = lookup(response_ref, raw_spec)
    if 'allOf' in response_descr:
        properties = merge_all(response_descr, raw_spec).get('properties', {})
    else:
        properties = response_descr.get('properties', {})

    column_names = get_col_name_from_prop(properties, raw_spec)
    return column_names


def check_iterable_v2(responses, route, http_method, raw_spec):
    # type (dict, str, str, dict) -> boolean
    """
    Check data structure it it is ana array for OpenAPI2.
    """
    result = False
    response_code = SUCCESS_CODES[http_method]
    if response_code in responses:
        response_200 = responses.get(response_code)
        if 'schema' in response_200:
            schema = response_200['schema']
            if '$ref' in schema:
                object_key = schema['$ref'].split('/')[-1]
                object_descr = raw_spec['definitions'][object_key]
                object_properties = object_descr['properties']
                data_structure = object_properties['data']
                result = data_structure.get('type') == 'array'
    return result


def check_iterable_v3(responses, route, http_method, raw_spec):
    # type (dict, str, str, dict) -> bool
    """
    Check data structure it it is ana array for OpenAPI3.
    """
    result = False
    if SUCCESS_CODES[http_method] in responses:
        response_200 = responses.get(SUCCESS_CODES[http_method])
        if "$ref" in response_200:
            response_200 = lookup(response_200['$ref'], raw_spec)
        if 'schema' in response_200["content"]["application/json"]:
            schema = response_200["content"]["application/json"]["schema"]
            if '$ref' in schema:
                schema = lookup(schema["$ref"], raw_spec)
            object_properties = schema['properties']
            data_structure = object_properties['data']
            result = data_structure.get('type') == 'array'
    return result


def get_response_ref_v2(raw_spec, route, http_method):
    # type: (dict, str, str) -> str
    """
    Get response reference for OpenAPI2.
    """
    response_ref = ''
    route_data = raw_spec['paths'][route]
    responses = route_data[http_method]['responses']
    response_code = SUCCESS_CODES[http_method]
    if response_code in responses:
        response_200 = responses[response_code]
        if 'schema' in response_200:
            schema = response_200['schema']
            if '$ref' in schema:
                response_ref = schema['$ref']
    return response_ref


def get_response_ref_v3(raw_spec, route, http_method):
    # type: (dict, str, str) -> str
    """
    Get response reference for OpenAPI3.
    """
    responses = raw_spec['paths'][route][http_method]['responses']
    response_200 = responses.get(SUCCESS_CODES[http_method])
    if '$ref' in response_200:
        response_200 = lookup(response_200['$ref'], raw_spec)
    result = response_200['content']['application/json']['schema']['$ref']
    return result


def get_body_type_params_v3(raw_spec, route, http_method):
    # type: (dict, str, str) -> dict
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

    param = {}  # type: dict
    route_data = raw_spec.get('paths', {}).get(route, {}).get(http_method, {})
    if "requestBody" in route_data:
        param = {}
        request_body = route_data['requestBody']
        raw_block = lookup(request_body.get("$ref"), raw_spec) if "$ref" in \
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


def get_spec(data):
    # type: (str) -> openapi.OpenAPIBaseSpec
    """
    Get specifications
    """
    # pylint: disable=no-else-return
    if is_openapi_v3(data):
        return openapi.OpenAPIv3Spec(data)
    return openapi.OpenAPIv2Spec(data)


def handle_oneof(data, obj_type=None):
    '''
    Returns full reference to object if obj_type is present inside oneOf block.
    Using for OpenAPI3 specification.
    '''
    oneof_ref = None
    list_typedata = data['oneOf']
    for type_dict in list_typedata:
        if '$ref' in type_dict and type_dict['$ref'].split('/')[-1] == obj_type:
            oneof_ref = type_dict['$ref']
    return oneof_ref


def read_spec(api_level, ext='json'):
    """
    Reads Scalr specification file, json or yaml.
    """

    spec_path = os.path.join(defaults.CONFIG_DIRECTORY,
                             '{}.{}'.format(api_level, ext))

    # pylint: disable=no-else-return
    if os.path.exists(spec_path):
        with open(spec_path, 'r') as fp:
            spec_data = fp.read()

        if ext == 'json':
            return json.loads(spec_data)
        elif ext == 'yaml':
            return yaml.safe_load(spec_data)
    else:
        msg = "Scalr specification file '{}' does  not exist, " \
              "try to run 'scalr-ctl update'.".format(spec_path)
        raise click.ClickException(msg)


def read_spec_openapi():
    """
    Reads Scalr specification file, json or yaml.
    """

    spec_path = os.path.join(defaults.CONFIG_DIRECTORY, 'openapi.json')

    # pylint: disable=no-else-return
    if os.path.exists(spec_path):
        with open(spec_path, 'r') as fp:
            spec_data = fp.read()

        return json.loads(spec_data)
    else:
        msg = "Scalr specification file '{}' does  not exist, " \
              "try to run 'scalr-ctl update'.".format(spec_path)
        raise click.ClickException(msg)


def read_routes():
    """
    Reads routes if exist
    """
    if os.path.exists(defaults.ROUTES_PATH):  # pylint: disable=no-member
        with open(defaults.ROUTES_PATH, 'r') as fp:  # pylint: disable=no-member
            api_routes = fp.read()
        return json.loads(api_routes)


def read_scheme():
    """
    Reads schema
    """
    with open(defaults.SCHEME_PATH) as fp:
        return json.load(fp)


def read_config(profile=None):
    """
    Reads config
    """
    confpath = os.path.join(
        defaults.CONFIG_DIRECTORY,
        '{}.yaml'.format(profile)
    ) if profile else defaults.CONFIG_PATH

    if os.path.exists(confpath):
        with open(confpath, 'r') as fp:
            return yaml.safe_load(fp)


def warning(*messages):
    """
    Prints the warning message(s) to stderr.

    :param tuple messages: The list of the warning messages.
    :rtype: None
    """
    color = 'yellow' if settings.colored_output else None
    for index, message in enumerate(messages or [], start=1):
        index = index if len(messages) > 1 else None
        code = message.get('code') or ''
        text = message.get('message') or ''
        click.secho("Warning{index}{code} {text}".format(
            index=' {}:'.format(index) if index else ':',
            code=' {}:'.format(code) if code else '',
            text=text
        ), err=True, fg=color)


def debug(msg):
    """
    Debug mode
    """
    if settings.debug_mode:
        click.secho("DEBUG: {}".format(msg),
                    fg='green' if settings.colored_output else None)


def reraise(message):
    """
    Reraise error message
    """
    exc_info = sys.exc_info()
    if isinstance(exc_info[1], click.ClickException):
        exc_class = exc_info[0]
    else:
        exc_class = click.ClickException
    debug(traceback.format_exc())
    message = str(message)
    if not settings.debug_mode:
        message = "{}\nUse '--debug' option for details.".format(message)
    raise exc_class(message)


def is_openapi_v3(data):
    """
    Method for detect openapi3
    """
    if "openapi" in data:
        return True
    return False


def lookup(response_ref, raw_spec):
    """
    Returns document section
    Example: #/definitions/Image returns Image defenition section.
    """
    result = None
    if response_ref.startswith('#'):
        paths = response_ref.split('/')[1:]
        result = raw_spec
        for path in paths:
            if path not in result:
                result = None
                break
            result = result[path]
    return result


def merge_allof(data, raw_spec):
    # type: (dict, dict) -> dict
    """
    Merge objects into one from allOf.
    """
    merged = {}  # type: dict
    for block in data:
        if "$ref" in block:
            block = lookup(block['$ref'], raw_spec)
        merge(block, merged)
    return merged


def merge(block, merged):
    # type: (dict, dict) -> dict
    """
    Merge values in block.
    """
    for k, v in block.items():
        if isinstance(v, list):
            if k not in merged:
                merged[k] = v
            else:
                merged[k] += v
                merged[k] = list(set(merged[k]))
        elif isinstance(v, dict):
            if k not in merged:
                merged[k] = v
            else:
                merged[k].update(v)
        else:
            merged[k] = v


def merge_anyof(data, raw_spec, object_name):
    # type: (list, dict, typing.Optional[str]) -> dict
    """
    Merge objects into one from anyOf.
    """
    merged = {}  # type: dict
    data = [a for a in data if a['$ref'].endswith(object_name)]
    for block in data:
        if "$ref" in block:
            block = lookup(block['$ref'], raw_spec)
            if 'allOf' in block:
                for value in block['allOf']:
                    merge(value, merged)
        else:
            merge(block, merged)
    return merged


def merge_all(data, raw_spec, object_name=None):
    # type: (dict, dict, str) -> dict
    """
    Returns merged data from received block.
    Uses in v3 specifications.
    """
    if "allOf" in data:
        merged = merge_allof(data['allOf'], raw_spec)
    elif "anyOf" in data:
        merged = merge_anyof(data['anyOf'], raw_spec, object_name)
    else:
        merged = data

    return merged


class _spinner(object):
    """
    Spinner
    """

    @staticmethod
    def draw(event):
        """
        Draw in console
        """
        if settings.colored_output:
            cursor = itertools.cycle('|/-\\')
            while not event.isSet():
                sys.stdout.write(next(cursor))
                sys.stdout.flush()
                time.sleep(0.1)
                sys.stdout.write('\b')
            sys.stdout.write(' ')
            sys.stdout.flush()

    def __init__(self):
        self.event = threading.Event()
        self.thread = threading.Thread(target=_spinner.draw,
                                       args=(self.event,))
        self.thread.daemon = True

    def __enter__(self):
        self.thread.start()

    def __exit__(self, _type, value, _traceback):
        self.event.set()
        self.thread.join()
