__author__ = 'Dmitriy Korsakov'

import os
import json
import pydoc

import yaml

from scalrctl import click
from scalrctl import commands
from scalrctl import settings
from scalrctl import defaults


class Import(commands.Action):

    def get_description(self):
        return "Import Scalr Objects"

    def get_options(self):
        argument = click.Argument(("id",), required=False)
        debug = click.Option(('--debug/--no-debug', 'debug'), default=False, help="Print debug messages")
        return [argument, debug]

    def run(self, *args, **kwargs):
        if "debug" in kwargs:
            settings.debug_mode = kwargs.pop("debug")

        raw = click.get_text_stream("stdin")

        obj = self._validate_object(raw)
        self.api_level = obj["meta"]["scalrctl"]["API_LEVEL"]
        self.http_method = obj["meta"]["scalrctl"]["METHOD"]
        self.route = obj["meta"]["scalrctl"]["route"]

        path = os.path.join(defaults.CONFIG_DIRECTORY, "%s.json" % self.api_level)
        self.raw_spec = json.load(open(path, "r"))

        with open(os.path.join(os.path.dirname(__file__), '../scheme/scheme.json')) as fp:
            scheme = json.load(fp)
            print scheme.keys()

        action_scheme = self._lookup_action(scheme, self.route, self.http_method)
        if action_scheme:
            if 'class' in action_scheme:
                cls = pydoc.locate(action_scheme['class'])
            else:
                cls = commands.Action
            action = cls(name=self.name, route= self.route, http_method="update", api_level=self.api_level)
            arguments = obj["meta"]["scalrctl"]['arguments']
            action.run(*arguments[0], **arguments[1])


    def _lookup_action(self, dct, route, http_method):
        if "route" in dct and dct["route"] == route and dct["http-method"] == http_method:
            return dct
        else:
            for k, v in dct.items():
                if isinstance(v, dict):
                    return self._lookup_action(v, route, http_method)
            return {}



    def _init(self):
        pass

    def _validate_object(self, yml):
        try:
            descr = yaml.load(yml)
            print "YAML:", descr
            assert "data" in descr
            assert "meta" in descr
            meta = descr["meta"]
            assert "scalrctl" in meta
            info = meta["scalrctl"]

            for key in (
                "METHOD",
                "route",
                "envId",
                "arguments",
                "API_LEVEL"
            ):
                assert key in info

            return descr

        except (Exception, BaseException), e:

            if settings.debug_mode:
                click.echo(e)
                click.echo(descr)

            raise click.ClickException("Invalid object description")
