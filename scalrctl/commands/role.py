__author__ = 'Dmitriy Korsakov'
__doc__ = 'Role management'

import copy
from scalrctl import commands
from scalrctl import click


class ChangeRoleAttrs(commands.Action):
    prompt_for = ["roleId"]


class RoleClone(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl role clone --roleId <ID> --name MyNewRole"
    post_template = {
        "cloneRoleRequest": {"name": ""}
    }

    def get_options(self):
        hlp = "The name of a new Role."
        new_name = click.Option(('--name', 'name'), required=True, help=hlp)
        options = [new_name, ]
        options.extend(super(RoleClone, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        name = kwargs.pop("name", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["cloneRoleRequest"]["name"] = name
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(RoleClone, self).pre(*args, **kv)
        return arguments, kw


class RolePromote(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl role promote --roleId <ID>"
    post_template = {
        "cloneRoleRequest": {"name": ""}
    }

    def get_options(self):
        hlp = "The name of a new Role."
        new_name = click.Option(('--name', 'name'), required=True, help=hlp)
        options = [new_name, ]
        options.extend(super(RoleClone, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        name = kwargs.pop("name", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["cloneRoleRequest"]["name"] = name
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(RoleClone, self).pre(*args, **kv)
        return arguments, kw


class RolePromote(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl role promote --roleId <ID>"
    post_template = {}

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kv = {"import-data": {}}
        kv.update(kwargs)
        arguments, kw = super(RolePromote, self).pre(*args, **kv)
        return arguments, kw


class RoleDeprecate(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl role deprecate --roleId <ID> --replacement <newRoleId>"
    post_template = {"deprecateRoleRequest": {"deprecate": True}}

    def get_options(self):
        hlp = "The suggested replacement RoleID for the current Role."
        replacement = click.Option(('--replacement', 'replacement'), required=False, help=hlp)
        state_hlp = "The deprecation state to set on the Role."
        state = click.Option(
            ('--state', 'state'), type=click.Choice(['DEPRECATED', 'ACTIVE']), required=True,help=state_hlp)
        options = [replacement, state]
        options.extend(super(RoleDeprecate, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        replacement = kwargs.pop("replacement", None)
        state = kwargs.pop("state")
        post_data = copy.deepcopy(self.post_template)
        if replacement:
            post_data["deprecateRoleRequest"]["replacement"] = {"id": replacement}
        if "ACTIVE" == state:
            post_data["deprecateRoleRequest"]["deprecate"] = False
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(RoleDeprecate, self).pre(*args, **kv)
        return arguments, kw