"""
Import Scalr objects.
"""
import json
import os
import pydoc

import yaml

from scalrctl import click, commands, settings, utils


__author__ = 'Dmitriy Korsakov'


class Import(commands.Action):

    action = None
    epilog = "Example: scalr-ctl import < object.yml"

    relations = {
        'script': {
            'script-versions.scriptId': 0,
        },
        'role-categories': {
            'role.category.id': 0,
        },
        'role': {
            'role-global-variables.roleId': 0,
            'role-orchestration-rule.roleId': 0,
            'role-images.roleId': 0,
        },
        'image': {
            'role-images.imageId': 0,
        }
    }

    def _init(self):
        self.scheme = utils.read_scheme()
        super(Import, self)._init()

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

        for obj in import_objects:
            action_name = obj['meta']['scalrctl']['ACTION']
            obj_name = obj['data'].get('name')
            result = None

            try:
                if action_name == 'role-categories':
                    # finds objects with the same names in new environment
                    result = self._find_existing_object(action_name, obj_name, env_id)

                if result:
                    msg = "Warning: \"{}\" already exists\n".format(obj_name)
                    click.secho(msg, bold=True, fg='yellow')
                else:
                    obj = self._modify_object(obj)  # updates object body with new ID's
                    result = self._import_object(obj, env_id, update_mode, dry_run)

                # save ID's of objects in new environment
                self._save_imported(obj, result['data'])
            except Exception as e:
                error_code = getattr(e, 'code', None)
                ignored = ('role-categories', 'role-global-variables')

                if error_code == 'UnicityViolation' and action_name in ignored:
                    click.secho("Warning: {}\n".format(str(e)), bold=True, fg='yellow')
                else:
                    # TODO: delete imported objects
                    raise click.ClickException(str(e))

    def _find_existing_object(self, action_name, obj_name, env_id):
        """
        Finds existing object with the same name in new environment.
        """

        list_data = self.scheme[action_name]['list']
        list_action = commands.Action(
            name=action_name,
            route=list_data['route'],
            http_method=list_data['http-method'],
            api_level=list_data['api_level'],
        )

        list_kwargs = {
            'envId': env_id,
            'name': obj_name,
            'hide_output': True
        }

        list_action_resp = list_action.run(**list_kwargs)
        resp_data = json.loads(list_action_resp).get('data')

        if resp_data and len(resp_data) > 0:
            if len(resp_data) == 1:
                return {'data': resp_data[0]}
            else:
                raise Exception("Matches for {} more than one!".format(action_name))

    def _import_object(self, obj_data, env_id, update_mode, dry_run=False):
        args, kwargs = obj_data['meta']['scalrctl']['ARGUMENTS']
        route = obj_data['meta']['scalrctl']['ROUTE']
        http_method = 'patch' if update_mode else 'post'
        obj_name = obj_data['data'].get('name')

        action = None
        for action_name, section in self.scheme['export'].items():
            if 'http-method' in section and 'route' in section and \
                            section['http-method'] == 'get' and \
                            section['route'] == route:
                scheme = section['{}-params'.format(http_method)]
                cls = pydoc.locate(
                    scheme['class']
                ) if 'class' in scheme else commands.Action
                action = cls(name=action_name, route=scheme['route'],
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

        click.secho("{} {} {} {}...".format(
            "Updating" if update_mode else "Creating",
            self._get_object_alias(obj_type),
            '\"%s\"' % obj_name if obj_name else '',
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
