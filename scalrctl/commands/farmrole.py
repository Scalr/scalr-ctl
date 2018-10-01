__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage FarmRoles'

import json
import copy

from scalrctl import commands
from scalrctl import click

from scalrctl import request, settings
from scalrctl.commands import farm


class LaunchServer(commands.SimplifiedAction):

    post_template = {}

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kv = {"import-data": {}}
        kv.update(kwargs)
        arguments, kw = super(LaunchServer, self).pre(*args, **kv)
        return arguments, kw


class FarmRoleClone(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl farm-roles clone --farmRoleId <ID> --alias <ALIAS> [--farmId <FarmID>]"

    post_template = {
        "cloneFarmRoleRequest": {"name": ""}
    }

    _table_columns = [u'alias', u'cloudPlatform', u'farm.id', u'id', u'instanceType.id',
                      u'role.id']

    def get_options(self):
        alias_hlp = "New alias name for the FarmRole being cloned."
        alias = click.Option(('--alias', 'alias'), required=True, help=alias_hlp)

        farm_hlp = "Identifier of the Farm to clone into. If omitted, current Farm is a target to clone the FarmRole."
        farm_id = click.Option(('--farmId', 'farm_id'), required=False, help=farm_hlp)

        options = [alias, farm_id]
        options.extend(super(FarmRoleClone, self).get_options())
        return options

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        name = kwargs.pop("alias", None)
        farm_id = kwargs.pop("farm_id", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["cloneFarmRoleRequest"]["name"] = name
        if farm_id:
            post_data["cloneFarmRoleRequest"]["farm"] = {}
            post_data["cloneFarmRoleRequest"]["farm"]["id"] = farm_id
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(FarmRoleClone, self).pre(*args, **kv)
        return arguments, kw


class FarmRoleCreateFromTemplate(farm.FarmCreateFromTemplate):

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kwargs = self._apply_arguments(**kwargs)
        stdin = kwargs.pop('stdin', None)
        kwargs["FarmRoleTemplate"] = self._read_object() if stdin else self._edit_example()
        return args, kwargs

    def _edit_example(self):
        commentary = \
            '''# The body must be a valid FarmRoleTemplate object.
#
# Type your FarmRoleTemplate object below this line. The above text will not be sent to the API server.'''
        text = click.edit(commentary)
        if text:
            raw_object = "".join([line for line in text.splitlines()
                                  if not line.startswith("#")]).strip()
        else:
            raw_object = ""
        return json.loads(raw_object)
