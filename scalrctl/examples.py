# -*- coding: utf-8 -*-
import os
import json
import re

from scalrctl import click, defaults

__author__ = 'Sergey Babak'


DOCS_HOST = 'https://api-explorer.scalr.com'

EXCLUDES = [
    '/{envId}/farm-roles/{farmRoleId}/servers/',
    '/{envId}/servers/',
]

DEFAULTS = {
    'string': '',
    'boolean': True,
    'integer': 1,
    'number': 1,
    'array': []
}


def _read_spec(api_level, extension="json"):
    text = None
    spec_path = os.path.join(defaults.CONFIG_DIRECTORY,
                             '{}.{}'.format(api_level, extension))
    if os.path.exists(spec_path):
        with open(spec_path, "r") as fp:
            text = fp.read()
    return text


def _item_by_ref(spec_data, ref):
    definition = ref.strip('/').split('/')[-1]
    if "openapi" in spec_data:  #v3
        return spec_data['components']['schemas'][definition]
    else:
        return spec_data['definitions'][definition]


def _generate_params(spec_data, schema):
    params = {}

    if '$ref' in schema:
        schema = _item_by_ref(spec_data, schema['$ref'])

    if 'properties' in schema:
        for p_key, p_value in schema['properties'].items():
            if p_value.get('readOnly'):
                continue
            if '$ref' in p_value:
                sub_item = _item_by_ref(spec_data, p_value['$ref'])
                params[p_key] = _generate_params(spec_data, sub_item)
            else:
                if 'enum' in p_value:
                    params[p_key] = p_value['enum'][0]
                else:
                    params[p_key] = DEFAULTS[p_value['type']]

    return params


def generate_post_data(spec_data, endpoint):
    """
    Generates POST data for specified API endpoint.
    """

    if "openapi" in spec_data:
        return _generate_post_data_v3(spec_data, endpoint)
    elif "basePath" in spec_data:
        return _generate_post_data_v2(spec_data, endpoint)
    else:
        raise click.ClickException("Unknown spec format")


def _generate_post_data_v2(spec_data, endpoint):
    if endpoint in spec_data['paths']:
        params_spec = spec_data['paths'].get(endpoint)
    else:
        raise click.ClickException('API endpoint {} does not found'.format(endpoint))

    if 'post' in params_spec:
        if 'parameters' in params_spec['post']:
            schema = params_spec['post']['parameters'][0]['schema']
            post_data = _generate_params(spec_data, schema)
        else:
            post_data = {}
    else:
        raise click.ClickException('POST method for endpoint {} does not exist'
                        .format(endpoint))
    return post_data


def _generate_post_data_v3(spec_data, endpoint):
    params_spec = spec_data['paths'].get(endpoint)
    if 'post' in params_spec:
        route_data = params_spec['post']
        if "requestBody" in route_data:
            schema = route_data["requestBody"]
            post_data = _generate_params(spec_data, schema)
        else:
            post_data = {}
        return post_data

'''
def get_body_type_params(self, route, http_method):
    result = []
    route_data = self.raw_spec['paths'][route][http_method]
    if "requestBody" in route_data:
        param = {}
        request_body = route_data['requestBody']
        raw_block = self._lookup(request_body.get("$ref")) if "$ref" in request_body else request_body
        param["schema"] = raw_block["content"]['application/json']["schema"]
        param["required"] = raw_block.get("required")
        param["description"] = raw_block.get("description")
        param["name"] = raw_block.get("name", param["schema"]['$ref'].split('/')[-1].lower())
        result.append(param)
    return result
'''

def get_definition(spec_data, endpoint):
    """
    Returns object name by endpoint.
    """
    if "openapi" in spec_data:
        return _get_definition_v3(spec_data, endpoint)
    elif "basePath" in spec_data:
        return _get_definition_v2(spec_data, endpoint)
    else:
        raise click.ClickException("Unknown spec format")

def _get_definition_v2(spec_data, endpoint):
    if endpoint in spec_data['paths']:
        endpoint_spec = spec_data['paths'].get(endpoint)
    else:
        raise click.ClickException('API endpoint {} does not found'.format(endpoint))
    for param in endpoint_spec['post'].get('parameters', ''):
        if '$ref' in param.get('schema', ''):
            result = param.get('schema')['$ref'].split('/')[-1]
            return result


def _get_definition_v3(spec_data, endpoint):
    route_data = spec_data['paths'][endpoint]["post"]
    request_body = route_data['requestBody']
    path = request_body.get("$ref")
    name = path.split('/')[-1]
    return name


def get_doc_url(api_level, endpoint):
    """
    Returns URL to documentation by API endpoint.
    """

    endpoint = endpoint.strip('/')

    # finds all path parameters
    params = re.findall(r'[{\[].*?}', endpoint)

    # creates postfix from last parameter
    last_param = params[-1] if params and endpoint.endswith(params[-1]) else ''
    postfix = '_{}'.format(last_param[1:-1]) if last_param else ''

    # removes all parameters from documentation path
    path = '/'.join(filter(lambda l: l not in params, endpoint.split('/')))

    return '{}/{}/{}/post{}.html'.format(DOCS_HOST, api_level, path, postfix)


def create_post_example(api_level, endpoint):
    """
    Returns example for POST request.
    """
    if endpoint in EXCLUDES:
        raise click.ClickException('Invalid API endpoint')

    spec_data = json.loads(_read_spec(api_level))
    post_data = generate_post_data(spec_data, endpoint)
    object_name = get_definition(spec_data, endpoint)
    doc_url = get_doc_url(api_level, endpoint)

    example = ("The body must be a valid {name} object. "
               "Example value:\n{post_data}\n"
               "See more at {doc_url}\n\n"
               "Type your {name} object below this line. "
               "The above text will not be sent to the API server.").format(
        name=object_name,
        post_data=json.dumps(post_data, indent=2),
        doc_url=doc_url,
    )
    example = '\n'.join(['# {}'.format(line) for line in example.split('\n')])
    return example
