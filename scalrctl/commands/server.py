__author__ = 'Dmitriy Korsakov'
__doc__ = 'Server management'
import copy
from scalrctl import commands
from scalrctl import click


class RebootServer(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl servers reboot --serverId <ID> --hard"

    post_template = {
        "serverRebootOptions": {"hard": True}
    }

    def get_options(self):
        hlp = "Reboot type. By default it does soft reboot unless this \
        option is set to true. Beware that some types of the instances do \
        not support soft reboot."
        hard_reboot = click.Option(('--hard', 'hard'), is_flag=True, default=False, help=hlp)
        options = [hard_reboot, ]
        options.extend(super(RebootServer, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        hard = kwargs.pop("hard", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["serverRebootOptions"]["hard"] = hard
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(RebootServer, self).pre(*args, **kv)
        return arguments, kw


class ResumeServer(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl servers resume --serverId <ID>"
    post_template = {}

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kv = {"import-data": {}}
        kv.update(kwargs)
        arguments, kw = super(ResumeServer, self).pre(*args, **kv)
        return arguments, kw


class SuspendServer(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl servers suspend  --serverId <ID>"
    post_template = {}

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kv = {"import-data": {}}
        kv.update(kwargs)
        arguments, kw = super(SuspendServer, self).pre(*args, **kv)
        return arguments, kw


class TerminateServer(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl servers terminate --serverId <ID> --force"
    post_template = {
        "serverTerminationOptions": {"force": True}
    }

    def get_options(self):
        hlp = "It is used to terminate the Server immediately ignoring scalr.system.server_terminate_timeout."
        force_terminate = click.Option(('--force', 'force'), is_flag=True, default=False, help=hlp)
        options = [force_terminate, ]
        options.extend(super(TerminateServer, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        force = kwargs.pop("force", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["serverTerminationOptions"]["force"] = force
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(TerminateServer, self).pre(*args, **kv)
        return arguments, kw


class LaunchServerAlias(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl servers launch --farmRoleId <ID>"
    post_template = {
        "serverLaunchRequest": {"farmRole": None}
    }

    def get_options(self):
        hlp = "Launch a new Server for the specified Farm Role."
        farm_role_id = click.Option(('--farmRoleId', 'farm_role_id'), required=True, help=hlp)
        options = [farm_role_id, ]
        options.extend(super(LaunchServerAlias, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        farm_role_id = kwargs.pop("farm_role_id", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["serverLaunchRequest"]["farmRole"] = farm_role_id
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(LaunchServerAlias, self).pre(*args, **kv)
        return arguments, kw


class ServerChangeInstanceType(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl servers change-instance-type --serverId <ID> --instanceType <TYPE>"
    post_template = {
        "instanceType": {"id": None}
    }

    def get_options(self):
        hlp = """Modify the Instance type of the Server. Server status before this
        action depends on CloudPlatform: - For EC2 and OpenStack instance type change
        requires server status "suspended". - For VMware instance type change requires
        server status "running" or "suspended"."""
        instance_type = click.Option(('--instanceType', 'instance_type'), required=True, help=hlp)
        options = [instance_type, ]
        options.extend(super(ServerChangeInstanceType, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        instance_type = kwargs.pop("instance_type")
        post_data = copy.deepcopy(self.post_template)
        post_data["instanceType"]["id"] = instance_type
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(ServerChangeInstanceType, self).pre(*args, **kv)
        return arguments, kw
