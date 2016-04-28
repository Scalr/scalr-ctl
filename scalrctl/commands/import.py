__author__ = 'Dmitriy Korsakov'

import os
import json
import pydoc

import yaml

from scalrctl import click
from scalrctl import commands
from scalrctl import settings


class Import(commands.Action):

    action = None
    epilog = "Example: scalr-ctl import < object.yml"

    def _init(self):
        super(Import, self)._init()

        with open(os.path.join(os.path.dirname(__file__), '../scheme/scheme.json')) as fp:
            self.scheme = json.load(fp)

    def get_description(self):
        return "Import Scalr Objects."

    def get_options(self):
        debug = click.Option(('--debug/--no-debug', 'debug'), default=False, help="Print debug messages")
        envid = click.Option(('--envId', 'env_id'), help="Environment ID")
        upd_helpmsg = "Update existing object instead of creating new."
        update = click.Option(('--update', 'update'), is_flag=True, default=False, help=upd_helpmsg)
        return [debug, update, envid]

    def run(self, *args, **kwargs):
        if "debug" in kwargs:
            settings.debug_mode = kwargs.pop("debug")
        env_id = kwargs.pop("env_id", None)

        raw = click.get_text_stream("stdin")
        obj_data = self._validate_object(raw)

        get_type_route = obj_data["meta"]["scalrctl"]["ROUTE"]
        http_method = "patch" if kwargs.pop("update", False) else "post"

        action_scheme = None
        for obj_name, section in self.scheme["export"].items():
            if obj_name != "group_descr" and section["http-method"] == "get" and section["route"] == get_type_route:
                action_scheme = section["%s-params" % http_method]

        if not action_scheme:
            raise click.ClickException("Cannot import Scalr object: API method (%s,%s) not found" % (
                action_scheme["http-method"],
                action_scheme["route"]))

        cls = pydoc.locate(action_scheme['class']) if 'class' in action_scheme else commands.Action
        action = cls(name=self.name, route=action_scheme['route'], http_method=http_method, api_level=self.api_level)
        arguments, kv = obj_data["meta"]["scalrctl"]['ARGUMENTS']
        kv["import-data"] = {action.get_body_type_params()[0]["name"]: obj_data["data"]}
        if env_id:
            kv["envId"] = env_id
        return action.run(*arguments, **kv)

    def _validate_object(self, yml):
        try:
            descr = yaml.load(yml)
            assert "data" in descr
            assert "meta" in descr
            meta = descr["meta"]
            assert "scalrctl" in meta
            info = meta["scalrctl"]

            for key in (
                "METHOD",
                "ROUTE",
                "envId",
                "ARGUMENTS",
                "API_LEVEL"
            ):
                assert key in info

            return descr

        except (Exception, BaseException) as e:

            if settings.debug_mode:
                click.echo(e)
                click.echo(descr)

            raise click.ClickException("Invalid object description")
