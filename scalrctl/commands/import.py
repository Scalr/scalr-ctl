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

    def _init(self):
        super(Import, self)._init()

        with open(os.path.join(os.path.dirname(__file__), '../scheme/scheme.json')) as fp:
            self.scheme = json.load(fp)

    def get_description(self):
        return "Import Scalr Objects"

    def get_options(self):
        debug = click.Option(('--debug/--no-debug', 'debug'), default=False, help="Print debug messages")
        upd_helpmsg = "Update existing object instead of creating new."
        update = click.Option(('--update', 'update'), default=False, help=upd_helpmsg)
        return [debug, update]

    def run(self, *args, **kwargs):
        if "debug" in kwargs:
            settings.debug_mode = kwargs.pop("debug")

        raw = click.get_text_stream("stdin")
        obj_data = self._validate_object(raw)

        get_type_route = obj_data["meta"]["scalrctl"]["ROUTE"]
        if "id" in obj_data and obj_data["id"]:
            http_method = "patch"
            route = get_type_route
        else:
            http_method = "post"
            route = self._get_patch_type_route(get_type_route=get_type_route)

        print route, self._get_patch_type_route(get_type_route=get_type_route)
        return

        if not route:
            raise click.ClickException("Cannot import Scalr object: API method (%s,%s) not found" % (http_method, route))

        action_scheme = self._lookup_action_scheme(self.scheme, route, http_method)

        if 'class' in action_scheme:
            cls = pydoc.locate(action_scheme['class'])
        else:
            cls = commands.Action

        self.action = cls(name=self.name, route=route, http_method=http_method, api_level=self.api_level)

        """
        # TODO: 1. Get ID name 2. Search for ID in user input 3. POST if ID is empty else PATCH
        """

        """
        self.api_level = obj["meta"]["scalrctl"]["API_LEVEL"]
        self.http_method = obj["meta"]["scalrctl"]["METHOD"]
        self.
        """

        arguments = obj_data["meta"]["scalrctl"]['arguments']  # XXX
        self.action.run(*arguments[0], **arguments[1])

    def _get_patch_type_route(self, get_type_route):
        """
        :param get_type_route: route of GET-method for Scalr object
        :returns route of POST-method for Scalr object
        Example: _get_patch_type_route("/images/{imageId}/") returns "/images/"
        """
        return get_type_route  # XXX

    def _lookup_action_scheme(self, dct, route, http_method):
        if "route" in dct and dct["route"] == route and dct["http-method"] == http_method:
            return dct
        else:
            for k, v in dct.items():
                if isinstance(v, dict):
                    return self._lookup_action_scheme(v, route, http_method)
            return {}

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
                "ROUTE",
                "envId",
                "ARGUMENTS",
                "API_LEVEL"
            ):
                assert key in info

            return descr

        except (Exception, BaseException), e:

            if settings.debug_mode:
                click.echo(e)
                click.echo(descr)

            raise click.ClickException("Invalid object description")
