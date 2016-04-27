__author__ = 'Dmitriy Korsakov'

import json
import datetime
import copy
from collections import OrderedDict

from scalrctl import settings
from scalrctl import commands
from scalrctl import click
from scalrctl import defaults

import yaml


class Export(commands.Action):

    def run(self, *args, **kwargs):
        kv = kwargs.copy()
        kv['hide_output'] = True
        response = super(Export, self).run(*args, **kv)

        kwargs["envId"] = settings.envId
        kv = copy.deepcopy(kwargs)
        for item in ("debug", "nocolor", "transformation"):
            if item in kv:
                del kv[item]
        uri = self._request_template.format(**kwargs)

        d = {
            "API_VERSION": settings.API_VERSION,
            "envId": settings.envId,
            "DATE": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "API_HOST": settings.API_HOST,
            "API_LEVEL": self.api_level,
            "METHOD": self.http_method,
            "ROUTE": self.route,
            "URI": uri,
            "ACTION": self.name,
            "ARGUMENTS": (args, kv),
            "SCALRCTL_VERSION": defaults.VERSION,
             }

        try:
            response_json = json.loads(response)
        except ValueError as e:
            if settings.debug_mode:
                raise
            raise click.ClickException(str(e))

        response_json["meta"]["scalrctl"] = d

        dump = yaml.safe_dump(
            response_json,
            encoding='utf-8',
            allow_unicode=True,
            default_flow_style=False
        )
        click.echo(dump)


class ExportFarmRoleGlobalVariable(Export):
    prompt_for = ["roleId", "globalVariableName"]


class ExportImage(Export):
    prompt_for = ["imageId"]