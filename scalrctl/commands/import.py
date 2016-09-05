"""
Import Scalr objects.
"""
import json
import os
import pydoc

import yaml

from scalrctl import click, commands, settings


__author__ = 'Dmitriy Korsakov'


class Import(commands.Action):

    action = None
    epilog = "Example: scalr-ctl import < object.yml"

    def _init(self):
        super(Import, self)._init()

        with open(os.path.join(os.path.dirname(__file__),
                               '../scheme/scheme.json')) as fp:
            self.scheme = json.load(fp)

    def get_description(self):
        return "Import Scalr Objects."

    def get_options(self):
        debug = click.Option(('--debug', 'debug'), is_flag=True,
                             default=False, help="Print debug messages")
        envid = click.Option(('--envId', 'env_id'), help="Environment ID")
        upd_helpmsg = "Update existing object instead of creating new."
        update = click.Option(('--update', 'update'), is_flag=True,
                              default=False, help=upd_helpmsg, hidden=True)
        dry_run = click.Option(('--dryrun', 'dryrun'), is_flag=True,
                               default=False, help=upd_helpmsg, hidden=True)
        return [debug, update, envid, dry_run]

    def run(self, *args, **kwargs):
        if 'debug' in kwargs:
            settings.debug_mode = kwargs.pop('debug')
        env_id = kwargs.pop("env_id", None) or settings.envId

        dry_run = kwargs.pop('dryrun', False)
        update_mode = kwargs.pop('update', False)

        raw_objects = kwargs.pop('raw', None) or click.get_text_stream('stdin')
        import_objects = self._validate_object(raw_objects)

        updated_args = {}
        for obj_data in import_objects:
            obj_data['meta']['scalrctl']['ARGUMENTS'][1].update(updated_args)
            result, alias = self._import_object(obj_data, env_id, update_mode, dry_run)

            if 'id' in result['data']:
                updated_args['{}Id'.format(alias)] = result['data']['id']

    def _import_object(self, obj_data, env_id, update_mode, dry_run=False):
        args, kwargs = obj_data['meta']['scalrctl']['ARGUMENTS']
        route = obj_data['meta']['scalrctl']['ROUTE']
        http_method = 'patch' if update_mode else 'post'

        action_scheme = None
        for obj_name, section in self.scheme['export'].items():
            if 'http-method' in section and 'route' in section and \
                            section['http-method'] == 'get' and \
                            section['route'] == route:
                action_scheme = section["{}-params".format(http_method)]

        if not action_scheme:
            msg = "Cannot import Scalr object: API method '{}: {}' not found" \
                .format('GET', route)
            raise click.ClickException(msg)

        cls = pydoc.locate(
            action_scheme['class']
        ) if 'class' in action_scheme else commands.Action
        action = cls(name=self.name, route=action_scheme['route'],
                     http_method=http_method, api_level=self.api_level)

        obj_type = action.get_body_type_params()[0]['name']
        kwargs['import-data'] = {obj_type: obj_data['data']}
        kwargs['dryrun'] = dry_run
        if env_id:
            kwargs['envId'] = env_id

        click.secho("{} {} {}".format(
            "Updating" if update_mode else "Creating",
            self._get_object_alias(obj_type),
            "ID" if update_mode else ""
        ), bold=True)

        result = action.run(*args, **kwargs)
        result_json = json.loads(result)

        alias = self._get_object_alias(obj_type)
        click.secho("{} created.\n".format(alias), bold=True)

        return result_json, alias

    @staticmethod
    def _get_object_alias(obj_type):
        """
        :return: "role" for "roleObject", "script" for "scriptObject"
        """
        if obj_type and obj_type.endswith("Object"):
            return obj_type[:-6]
        else:
            return obj_type

    @staticmethod
    def _validate_object(raw_objects):
        import_objects = yaml.safe_load(raw_objects)
        for obj_data in import_objects:
            assert 'data' in obj_data
            assert 'meta' in obj_data
            assert 'scalrctl' in obj_data['meta']
            meta_info = obj_data['meta']['scalrctl']
            for key in ('METHOD',
                        'ROUTE',
                        'envId',
                        'ARGUMENTS',
                        'API_LEVEL'):
                assert key in meta_info
        return import_objects


class ImportImage(commands.Action):

    def pre(self, *args, **kwargs):
        if 'imageId' not in kwargs:
            kwargs['image'] = click.termui.prompt("Image object JSON")

        return super(commands.Action, self).pre(*args, **kwargs)


class UpdateImage(commands.Action):
    mutable_body_parts = ['name']
    prompt_for = ['imageId']
