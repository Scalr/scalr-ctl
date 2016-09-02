"""
Export Scalr objects.
"""
import copy
import datetime
import json

import yaml

from scalrctl import click, commands, defaults, settings


__author__ = 'Dmitriy Korsakov'


class Export(commands.Action):

    def _get_custom_options(self):
        # Disable output modifiers
        options = []
        debug = click.Option(('--debug', 'debug'), is_flag=True,
                             default=False, help="Print debug messages")
        options.append(debug)
        return options

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

        data = {
            'meta': {
                'scalrctl': scalrctl_meta
            },
            'include': [
                response_json,
            ]
        }

        if not hide_output:
            dump = yaml.safe_dump(
                data, encoding='utf-8',
                allow_unicode=True,
                default_flow_style=False
            )
            click.echo(dump)
        return data


class ExportFarmRoleGlobalVariable(Export):
    prompt_for = ['roleId', 'globalVariableName']


class ExportImage(Export):
    prompt_for = ['imageId']


class ExportScript(Export):

    def run(self, *args, **kwargs):
        # TODO: help for update! (some script-versions may be deleted)
        # interactive update by default (prompt for deletes and updates),
        # with optional force
        kwargs['hide_output'] = True
        response = super(ExportScript, self).run(*args, **kwargs)

        sv_list_action = commands.Action(
            'script-version',
            '/{envId}/scripts/{scriptId}/script-versions/',
            'get',
            'user'
        )
        sv_list_resp = sv_list_action.run(
            envId=kwargs['envId'],
            scriptId=kwargs['scriptId'],
            hide_output=True
        )
        sv_list_json = json.loads(sv_list_resp)

        sv_get_action = Export(
            'script-version',
            '/{envId}/scripts/{scriptId}/'
            'script-versions/{scriptVersionNumber}/',
            'get',
            'user',
        )

        for script in sv_list_json['data']:
            if script.get('body'):
                resp = sv_get_action.run(
                    envId=kwargs['envId'],
                    scriptId=kwargs['scriptId'],
                    scriptVersionNumber=script['version'],
                    hide_output=True
                )
                for item in resp['include']:
                    response['include'].append(item)

        dump = yaml.safe_dump(
            response,
            encoding='utf-8',
            allow_unicode=True,
            default_flow_style=False
        )
        click.echo(dump)

        #click.echo(json.dumps(response, indent=2))
        return response
