__author__ = 'Dmitriy Korsakov'

import json
import datetime
import copy

from scalrctl import settings
from scalrctl import commands
from scalrctl import click

import yaml


class Export(commands.Action):

    def run(self, *args, **kwargs):
        kv = kwargs.copy()
        kv['hide_output'] = True
        response = super(Export, self).run(*args, **kv)

        kwargs["envId"] = settings.envId

        uri = self._request_template.format(**kwargs)

        kv = copy.deepcopy(kwargs)
        for item in ("debug", "nocolor", "transformation"):
            if item in kv:
                del kv[item]

        d = {
            "API_VERSION": settings.API_VERSION,
            "envId": settings.envId,
            "date": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "API_HOST": settings.API_HOST,
            "METHOD": self.http_method,
            "route": self.route,
            "URI": uri,
            "action": self.name,
            "arguments": (args, kv)
             }

        try:
            response_json = json.loads(response)
        except ValueError, e:
            if settings.debug_mode:
                raise
            raise click.ClickException(str(e))

        response_json["meta"]["scalrctl"] = d
        dump = yaml.safe_dump(response_json, encoding='utf-8', allow_unicode=True, default_flow_style=False)
        click.echo(dump)


class ExportFarmRoleGlobalVariable(Export):
    prompt_for = ["roleId", "globalVariableName"]


class ExportImage(Export):
    prompt_for = ["imageId"]