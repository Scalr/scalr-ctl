__author__ = 'Dmitriy Korsakov'
__doc__ = 'Role management'

import copy
from scalrctl import commands
from scalrctl import click


class ChangeRoleAttrs(commands.Action):
    prompt_for = ["roleId"]


class RoleClone(commands.Action):

    epilog = "Example: scalr-ctl role clone --roleId <ID> --name MyNewRole"
    post_template = {
        "cloneRoleRequest": {"name": ""}
    }
    ignored_options = ("stdin",)

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


class RolePromote(commands.Action):

    epilog = "Example: scalr-ctl role promote --roleId <ID>"
    post_template = {
        "cloneRoleRequest": {"name": ""}
    }
    ignored_options = ("stdin",)

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


class RolePromote(commands.Action):

    epilog = "Example: scalr-ctl role promote --roleId <ID>"
    post_template = {}
    ignored_options = ("stdin",)

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kv = {"import-data": {}}
        kv.update(kwargs)
        arguments, kw = super(RolePromote, self).pre(*args, **kv)
        return arguments, kw