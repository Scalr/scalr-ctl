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

    relations = {
        'script': {
            'script-version.scriptId': 0,
        },
        'role-category': {
            'role.category.id': 0,
        },
        'role': {
            'role-global-variables.roleId': 0,
            'role-orchestration-rule.roleId': 0,
            'role-image.roleId': 0,
        },
        'image': {
            'role-image.imageId': 0,
        }
    }

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

    def _modify_object(self, obj):
        arguments = {}
        action_name = obj['meta']['scalrctl']['ACTION']

        for params in self.relations.values():
            for key, value in params.items():
                if not value:
                    continue
                head, _, tail = key.partition('.')
                if head == action_name:
                    if '.' not in tail and tail.endswith('Id'):
                        arguments.update({tail: value})
                    else:
                        data = value
                        for item in reversed(tail.split('.')):
                            data = {item: data}
                        obj['data'].update(data)

        obj['meta']['scalrctl']['ARGUMENTS'][1].update(arguments)

        return obj

    def _save_imported(self, obj, data):
        action_name = obj['meta']['scalrctl']['ACTION']
        for key, value in self.relations.get(action_name, {}).items():
            self.relations[action_name][key] = data['id']

    def run(self, *args, **kwargs):
        if 'debug' in kwargs:
            settings.debug_mode = kwargs.pop('debug')
        env_id = kwargs.pop('env_id', None) or settings.envId

        dry_run = kwargs.pop('dryrun', False)
        update_mode = kwargs.pop('update', False)

        raw_objects = kwargs.pop('raw', None) or click.get_text_stream('stdin')
        import_objects = self._validate_object(raw_objects)

        try:
            for obj in import_objects:
                obj = self._modify_object(obj)
                result = self._import_object(obj, env_id, update_mode, dry_run)
                self._save_imported(obj, result['data'])
        except Exception as e:
            # TODO: delete imported objects
            raise click.ClickException(str(e))

    def _import_object(self, obj_data, env_id, update_mode, dry_run=False):
        args, kwargs = obj_data['meta']['scalrctl']['ARGUMENTS']
        route = obj_data['meta']['scalrctl']['ROUTE']
        http_method = 'patch' if update_mode else 'post'

        action = None
        for obj_name, section in self.scheme['export'].items():
            if 'http-method' in section and 'route' in section and \
                            section['http-method'] == 'get' and \
                            section['route'] == route:
                scheme = section['{}-params'.format(http_method)]
                cls = pydoc.locate(
                    scheme['class']
                ) if 'class' in scheme else commands.Action
                action = cls(name=obj_name, route=scheme['route'],
                             http_method=http_method, api_level=self.api_level)
                break

        if not action:
            msg = "Cannot import Scalr object: API method '{}: {}' not found" \
                .format('GET', route)
            raise click.ClickException(msg)

        obj_type = action._get_body_type_params()[0]['name']
        if action.name not in ('role-image',):
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

        return result_json

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
        objects = yaml.safe_load(raw_objects)

        for obj in objects:
            assert 'data' in obj
            assert 'meta' in obj
            assert 'scalrctl' in obj['meta']
            meta_info = obj['meta']['scalrctl']
            for key in ('METHOD',
                        'ROUTE',
                        'envId',
                        'ARGUMENTS',
                        'API_LEVEL'):
                assert key in meta_info
        return objects


class ImportImage(commands.Action):

    def pre(self, *args, **kwargs):
        if 'imageId' not in kwargs:
            kwargs['image'] = click.termui.prompt("Image object JSON")

        return super(commands.Action, self).pre(*args, **kwargs)


class UpdateImage(commands.Action):
    mutable_body_parts = ['name']
    prompt_for = ['imageId']
