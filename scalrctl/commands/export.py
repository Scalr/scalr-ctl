"""
Export Scalr objects.
"""
import os
import copy
import datetime
import json
import pydoc

import yaml

from scalrctl import click, commands, defaults, settings


__author__ = 'Dmitriy Korsakov, Sergey Babak'


class Export(commands.Action):

    relations = {}

    def _get_custom_options(self):
        # Disable output modifiers
        options = []
        debug = click.Option(('--debug', 'debug'), is_flag=True,
                             default=False, help="Print debug messages")
        options.append(debug)
        return options

    @staticmethod
    def _get_param(parent, child, key):
        head, _, tail = key.partition('.')
        if head == 'child':
            return reduce(dict.__getitem__, tail.split('.'), child)
        elif head == 'parent':
            return reduce(dict.__getitem__, tail.split('.'), parent)
        else:
            raise Exception("Invalid key: \"{}\"".format(key))

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
            # TODO: recursive export
            # export_cls = pydoc.locate(
            #   scheme['export'][relation]['class']
            # ) if 'class' in scheme['export'][relation] else Export
            get_action = Export(
                name=relation,
                route=get_data['route'],
                http_method=get_data['http-method'],
                api_level=get_data['api_level'],
            )

            list_kwargs = {'hide_output': True}
            for key, value in relation_values['list'].items():
                list_kwargs[key] = self._get_param(parent, None, value)

            list_action_resp = list_action.run(**list_kwargs)
            resp_json = json.loads(list_action_resp)

            for obj_data in resp_json['data']:
                get_kwargs = {'hide_output': True}
                for key, value in relation_values['get'].items():
                    get_kwargs[key] = self._get_param(parent, obj_data, value)
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

        def _order(arg):
            action_name = arg['meta']['scalrctl']['ACTION']
            return self.relations.get(action_name, {}).get('order', 0)

        result = sorted(result, key=_order)

        if not hide_output:
            dump = yaml.safe_dump(
                result,
                encoding='utf-8',
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
        'script-versions': {
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
        'role-categories': {
            'order': -1,
            'get': {
                'roleCategoryId': 'child.id',
            },
            'list': {
                'scope': 'parent.scope'
            },
        },
        'role-orchestration-rules': {
            'get': {
                'roleId': 'parent.id',
                'orchestrationRuleId': 'child.id',
            },
            'list': {
                'roleId': 'parent.id'
            }
        },
        'role-global-variables': {
            'get': {
                'globalVariableName': 'child.name',
                'roleId': 'parent.id'
            },
            'list': {
                'roleId': 'parent.id',
                'declaredIn': 'parent.scope'
            }
        },
        'role-images': {
            'get': {
                'roleId': 'child.role.id',
                'imageId': 'child.image.id',
            },
            'list': {
                'roleId': 'parent.id'
            },
        },
    }


class ExportRoleImage(Export):

    relations = {
        'images': {
            'order': -1,
            'get': {
                'imageId': 'parent.id',
            },
            'list': {
                'id': 'parent.id',
            },
        },
    }
