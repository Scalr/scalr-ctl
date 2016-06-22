__author__ = 'Dmitriy Korsakov'

import json
import datetime
import copy

from scalrctl import settings
from scalrctl import commands
from scalrctl import click
from scalrctl import defaults

import yaml


class Export(commands.Action):

    def _get_custom_options(self):
        # Disable output modifiers
        options = []
        debug = click.Option(('--debug/--no-debug', 'debug'), default=False, help="Print debug messages")
        options.append(debug)
        return options

    def run(self, *args, **kwargs):
        hide_output = kwargs.pop("hide_output", False)

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
        if not hide_output:
            click.echo(dump)
        return response_json


class ExportFarmRoleGlobalVariable(Export):
    prompt_for = ["roleId", "globalVariableName"]


class ExportImage(Export):
    prompt_for = ["imageId"]


class ExportScript(Export):

    def run(self, *args, **kwargs):
        # TODO: help for update! (some script-versions may be deleted)
        # interactive update by default (prompt for deletes and updates), with optional force
        kwargs["hide_output"] = True
        response = super(ExportScript, self).run(*args, **kwargs)

        svlist_action = commands.Action(
            "script-version",
            "/{envId}/scripts/{scriptId}/script-versions/",
            "get",
            "user"
        )
        svlist_text = svlist_action.run(envId=kwargs["envId"], scriptId=kwargs["scriptId"], hide_output=True)
        svlist_dict = json.loads(svlist_text)
        svlist = svlist_dict["data"]

        svget_action = Export(
            "script-version",
            "/{envId}/scripts/{scriptId}/script-versions/{scriptVersionNumber}/",
            "get",
            "user"
        )
        include = []
        for sv in svlist:
            script_version = sv["version"]
            sctipt_body = sv["body"]
            if sctipt_body:
                out = svget_action.run(
                    envId=kwargs["envId"],
                    scriptId=kwargs["scriptId"],
                    scriptVersionNumber=script_version,
                    hide_output=True
                )
                include.append(out)

        response["include"] = include

        dump = yaml.safe_dump(
            response,
            encoding='utf-8',
            allow_unicode=True,
            default_flow_style=False
        )
        click.echo(dump)
        return response
