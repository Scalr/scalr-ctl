__author__ = 'Dmitriy Korsakov'
__doc__ = 'Farm management'

import copy

from scalrctl import commands
from scalrctl import click


class FarmTerminate(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl farms terminate --farmId <ID> --force"

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


class FarmLaunch(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl farms launch --farmId <ID>"
    post_template = {}

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kv = {"import-data": {}}
        kv.update(kwargs)
        arguments, kw = super(FarmLaunch, self).pre(*args, **kv)
        return arguments, kw


class FarmClone(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl farms clone --farmId <ID> --name MyNewFarm"
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


class FarmSuspend(FarmLaunch):

    epilog = "Example: scalr-ctl farms suspend --farmId <ID>"
    post_template = {}


class FarmResume(FarmLaunch):

    epilog = "Example: scalr-ctl farms resume --farmId <ID>"
    post_template = {}


class FarmLock(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl farm lock --farmId <ID> --comment <COMMENT> --unlock-permission <ANYONE|OWNER|TEAM>"

    post_template = {
        "lockFarmRequest": {"lockComment": "", "unlockPermission": "anyone"}
    }

    def get_options(self):
        comment = click.Option(('--lockComment', 'comment'), default="", help="Comment to lock a Farm.")
        hlp = "If you would like to prevent other users unlocking the Farm you should set 'owner' options.\
                  With 'team' options only members of the Farm's Teams can unlock this Farm.\
                  Default value 'anyone' means that anyone with access can unlock this Farm."
        unlock_permission = click.Option((
            '--unlockPermission', 'unlock_permission'),
            default="anyone", show_default=True, help=hlp)
        options = [comment, unlock_permission]
        options.extend(super(FarmLock, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        comment = kwargs.pop("comment", None)
        unlock_permission = kwargs.pop("unlock_permission", "anyone")
        post_data = copy.deepcopy(self.post_template)
        post_data["lockFarmRequest"]["lockComment"] = comment
        post_data["lockFarmRequest"]["unlockPermission"] = unlock_permission
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(FarmLock, self).pre(*args, **kv)
        return arguments, kw