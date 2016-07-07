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
        update = click.Option(('--update', 'update'), is_flag=True, default=False, help=upd_helpmsg, hidden=True)
        dry_run = click.Option(('--dryrun', 'dryrun'), is_flag=True, default=False, help=upd_helpmsg, hidden=True)
        return [debug, update, envid, dry_run]

    def run(self, *args, **kwargs):
        if "debug" in kwargs:
            settings.debug_mode = kwargs.pop("debug")
        if "dryrun" in kwargs:
            dry_run_mode = kwargs.pop("dryrun")

        env_id = kwargs.pop("env_id", None) or settings.envId
        raw = kwargs.pop("raw", None) or click.get_text_stream("stdin")
        obj_data = self._validate_object(raw)

        get_type_route = obj_data["meta"]["scalrctl"]["ROUTE"]
        update_mode = kwargs.pop("update", False)
        http_method = "patch" if update_mode else "post"

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

        obj_type = action.get_body_type_params()[0]["name"]
        kv["import-data"] = {obj_type: obj_data["data"]}
        if env_id:
            kv["envId"] = env_id
        if dry_run_mode:
            kv["dryrun"] = dry_run_mode

        click.echo("\x1b[1m%s %s %s\x1b[0m" % (
            "Updating" if update_mode else "Creating",
            self._get_object_alias(obj_type),
            "ID" if update_mode else ""  # TBD: ID
        ))
        click.echo()

        result = action.run(*arguments, **kv)
        result_json = json.loads(result)

        if "include" in obj_data:
            included_objects = obj_data["include"]

            for obj in included_objects:

                if obj["meta"]["scalrctl"]["ACTION"] == "script-version":  # XXX
                    obj["meta"]["scalrctl"]['ARGUMENTS'][1]['scriptId'] = result_json["data"]["id"]

                inc_raw = yaml.dump(obj)
                inc_kv = {
                    "debug": settings.debug_mode,
                    "env_id": env_id,
                    "dryrun": dry_run_mode,
                    "update": update_mode,
                    "raw": inc_raw,
                }

                self.run(**inc_kv)
        click.echo("\x1b[1m %s created. \x1b[0m" % self._get_object_alias(obj_type))
        click.echo()
        return result

    def _get_object_alias(self, obj_type):
        """
        :return: "role" for "roleObject", "script" for "scriptObject"
        """
        return obj_type[:-6] if obj_type and obj_type.endswith("Object") else obj_type



    def _validate_object(self, yml):
        try:
            descr = yaml.safe_load(yml)
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


class ImportImage(commands.Action):

    def pre(self, *args, **kwargs):
        if 'imageId' not in kwargs:
            kwargs["image"] = click.termui.prompt("Image object JSON")

        return super(commands.Action, self).pre(*args, **kwargs)


class UpdateImage(commands.Action):
    mutable_body_parts = ["name"]
    prompt_for = ["imageId"]
