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
        update = click.Option(('--update', 'update'), is_flag=True, default=False, help=upd_helpmsg)
        return [debug, update]

    def run(self, *args, **kwargs):
        if "debug" in kwargs:
            settings.debug_mode = kwargs.pop("debug")

        raw = click.get_text_stream("stdin")
        obj_data = self._validate_object(raw)

        get_type_route = obj_data["meta"]["scalrctl"]["ROUTE"]

        if "update" in kwargs:
            update = kwargs.pop("update")

            if update:
                http_method = "patch"
                route = get_type_route
            else:
                http_method = "post"
                route = self._get_post_type_route(self.scheme, get_type_route=get_type_route)
                print "GET route: %s,POST route: %s" % (get_type_route, route)

        if not route:
            raise click.ClickException("Cannot import Scalr object: API method (%s,%s) not found" % (
                http_method, route))

        action_scheme = self._lookup_action_scheme(self.scheme, route, http_method)

        if 'class' in action_scheme:
            cls = pydoc.locate(action_scheme['class'])
        else:
            cls = commands.Action

        self.action = cls(name=self.name, route=route, http_method=http_method, api_level=self.api_level)

        arguments = obj_data["meta"]["scalrctl"]['ARGUMENTS']  # XXX
        # self.action.run(*arguments[0], **arguments[1])

    def _get_post_type_route(self, dct, get_type_route):
        """
        :param get_type_route: route of GET-method for Scalr object
        :returns route of POST-method for Scalr object
        Example: _get_patch_type_route("/images/{imageId}/") returns "/images/"
        """
        found = False
        patch_route = None
        for k, v in dct.items():
            is_action = "class" in v
            is_object = "group_descr" in v
            is_level = not is_action and not is_object
            if is_action:
                continue
            elif is_object:
                for action, block in v.items():
                    if "route" in block and "http-method" in block:
                        if block["http-method"] == "get" and block["route"] == get_type_route:
                            found = True
                            continue
                        elif block["http-method"] == "post" and get_type_route.startswith(block["route"]):
                            patch_route = block["route"]
            if found:
                return patch_route
            elif is_level:
                patch_route = self._get_post_type_route(v, get_type_route)
                if patch_route:
                    return patch_route

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
