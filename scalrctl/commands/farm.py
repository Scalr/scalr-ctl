__author__ = 'Dmitriy Korsakov'
__doc__ = 'Farm management'

import copy

from scalrctl import commands
from scalrctl import click


class FarmTerminate(commands.Action):

    epilog = "Example: scalr-ctl farm terminate --farmId <ID> --force"

    post_template = {
        "terminateFarmRequest": {"force": True}
    }

    def get_options(self):
        hlp = "It is used to terminate the Server immediately ignoring scalr.system.server_terminate_timeout."
        force_terminate = click.Option(('--force', 'force'), is_flag=True, default=False, help=hlp)
        options = [force_terminate, ]
        options.extend(super(FarmTerminate, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        force = kwargs.pop("force", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["terminateFarmRequest"]["force"] = force
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(FarmTerminate, self).pre(*args, **kv)
        return arguments, kw


class FarmLaunch(commands.Action):

    epilog = "Example: scalr-ctl farm launch --farmId <ID>"
    post_template = {}

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kv = {"import-data": {}}
        kv.update(kwargs)
        arguments, kw = super(FarmLaunch, self).pre(*args, **kv)
        return arguments, kw


class FarmClone(commands.Action):

    epilog = "Example: scalr-ctl farm clone --farmId <ID> --name MyNewFarm"
    post_template = {
        "cloneFarmRequest": {"name": ""}
    }

    def get_options(self):
        hlp = "The name of a new Farm."
        hard_terminate = click.Option(('--name', 'name'), required=True, help=hlp)
        options = [hard_terminate, ]
        options.extend(super(FarmClone, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        name = kwargs.pop("name", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["cloneFarmRequest"]["name"] = name
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(FarmClone, self).pre(*args, **kv)
        return arguments, kw
