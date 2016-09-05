"""
Export Scalr objects.
"""
import os
import copy
import datetime
import json

import yaml

from scalrctl import click, commands, defaults, settings


__author__ = 'Dmitriy Korsakov, Sergey Babak'


def _recursive_get(d, key):
    if type(d) != dict:
        return
    head, _, tail = key.partition('.')
    h_value = d.get(head, '')
    if tail and type(h_value) == dict:
        return _recursive_get(h_value, tail)
    if not tail:
        return h_value


def parse_kwargs(parent, child, key):
    head, _, tail = key.partition('.')
    if head == 'child':
        return _recursive_get(child, tail)
    elif head == 'parent':
        return _recursive_get(parent, tail)
    else:
        raise Exception("Invalid relations key: \"{}\"".format(key))


class Export(commands.Action):

    relations = []

    def _get_custom_options(self):
        # Disable output modifiers
        options = []
        debug = click.Option(('--debug', 'debug'), is_flag=True,
                             default=False, help="Print debug messages")
        options.append(debug)
        return options

    def _get_relations(self, parent):

        with open(os.path.join(os.path.dirname(__file__),
                               '../scheme/scheme.json')) as fp:
            scheme = json.load(fp)

        data = []
        for relation, relation_values in self.relations.items():
            list_data = scheme[relation]['list']
            list_action = commands.Action(
                name=relation,
                route=list_data['route'],
                http_method=list_data['http-method'],
                api_level=list_data['api_level'],
            )

            get_data = scheme[relation]['get']
            get_action = Export(
                name=relation,
                route=get_data['route'],
                http_method=get_data['http-method'],
                api_level=get_data['api_level'],
            )

            list_kwargs = {'hide_output': True}
            for key, value in relation_values['list'].items():
                list_kwargs[key] = parse_kwargs(parent, None, value)

            list_action_resp = list_action.run(**list_kwargs)
            resp_json = json.loads(list_action_resp)

            for obj_data in resp_json['data']:
                get_kwargs = {'hide_output': True}
                for key, value in relation_values['get'].items():
                    get_kwargs[key] = parse_kwargs(parent, obj_data, value)
                resp = get_action.run(**get_kwargs)
                data.extend(resp)

        return data

    def run(self, *args, **kwargs):
        hide_output = kwargs.pop('hide_output', False)

        kv = kwargs.copy()
        kv['hide_output'] = True
        response = super(Export, self).run(*args, **kv)

        kwargs['envId'] = settings.envId
        kv = copy.deepcopy(kwargs)
        for item in ('debug', 'nocolor', 'transformation'):
            if item in kv:
                del kv[item]
        uri = self._request_template.format(**kwargs)

        scalrctl_meta = {
            'API_VERSION': settings.API_VERSION,
            'envId': settings.envId,
            'DATE': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'API_HOST': settings.API_HOST,
            'API_LEVEL': self.api_level,
            'METHOD': self.http_method,
            'ROUTE': self.route,
            'URI': uri,
            'ACTION': self.name,
            'ARGUMENTS': (args, kv),
            'SCALRCTL_VERSION': defaults.VERSION,
        }

        try:
            response_json = json.loads(response)
        except ValueError as e:
            if settings.debug_mode:
                raise
            raise click.ClickException(str(e))

        response_json['meta']['scalrctl'] = scalrctl_meta

        result = [response_json, ]
        if self.relations:
            relations = self._get_relations(response_json['data'])
            result.extend(relations)

        if not hide_output:
            dump = yaml.safe_dump(
                result, encoding='utf-8',
                allow_unicode=True,
                default_flow_style=False
            )
            click.echo(dump)

        return result


class ExportFarmRoleGlobalVariable(Export):
    prompt_for = ['roleId', 'globalVariableName']


class ExportImage(Export):
    prompt_for = ['imageId']


class ExportScript(Export):

    relations = {
        'script-version': {
            'get': {
                'scriptId': 'parent.id',
                'scriptVersionNumber': 'child.version',
            },
            'list': {
                'scriptId': 'parent.id'
            }
        },
    }


class ExportRole(Export):

    relations = {
        'role-image': {
            'get': {
                'roleId': 'child.role.id',
                'imageId': 'child.image.id',
            },
            'list': {
                'roleId': 'parent.id'
            }
        },
        'role-category': {
            'get': {
                'roleCategoryId': 'child.id',
            },
            'list': {
                'scope': 'parent.scope'
            }
        },
        'role-global-variables': {
            'get': {
                'globalVariableName': 'child.name',
                'roleId': 'parent.id'
            },
            'list': {
                'roleId': 'parent.id'
            }
        },
        'role-orchestration-rule': {
            'get': {
                'roleId': 'parent.id',
                'orchestrationRuleId': 'child.id',
            },
            'list': {
                'roleId': 'parent.id'
            }
        },
    }
