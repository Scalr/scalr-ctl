__author__ = 'Dmitriy Korsakov'
__doc__ = 'Server management'
import copy
import json
import time
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

    epilog = "Example: scalr-ctl servers resume --serverId <ID> --nowait"
    post_template = {}

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kv = {"import-data": {}}
        kv.update(kwargs)
        arguments, kw = super(ResumeServer, self).pre(*args, **kv)
        return arguments, kw

    def get_options(self):
        nowait_hlp = "Do not wait for server to resume"
        nowait = click.Option(('--nowait', 'nowait'), is_flag=True, required=False, help=nowait_hlp)
        options = [nowait, ]
        options.extend(super(ResumeServer, self).get_options())
        return options

    def run(self, *args, **kwargs):
        nowait = kwargs.pop("nowait", False)
        result = super(ResumeServer, self).run(*args, **kwargs)
        if not nowait:
            result_json = json.loads(result)
            server_id = result_json["data"]["id"]
            cls = commands.Action
            action = cls(name=self.name,
                         route="/{envId}/servers/{serverId}/",
                         http_method="get",
                         api_level="user")
            status = "suspended"
            click.echo("Waiting for server %s to resume.." % server_id)
            while status in ("suspended", "resuming"):
                data = action.run(**{"serverId": server_id, "hide_output": True,
                                     "envId": kwargs.get('envId')})
                data_json = json.loads(data)
                status = data_json["data"]["status"]
                time.sleep(1)
            click.echo("Server %s resumed." % server_id)

        return result


class SuspendServer(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl servers suspend  --serverId <ID> --nowait"
    post_template = {}

    def get_options(self):
        nowait_hlp = "Do not wait for server to reach 'suspended' state"
        nowait = click.Option(('--nowait', 'nowait'), is_flag=True, required=False, help=nowait_hlp)
        options = [nowait, ]
        options.extend(super(SuspendServer, self).get_options())
        return options

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kv = {"import-data": {}}
        kv.update(kwargs)
        arguments, kw = super(SuspendServer, self).pre(*args, **kv)
        return arguments, kw

    def run(self, *args, **kwargs):
        nowait = kwargs.pop("nowait", False)
        result = super(SuspendServer, self).run(*args, **kwargs)
        if not nowait:
            result_json = json.loads(result)
            server_id = result_json["data"]["id"]
            cls = commands.Action
            action = cls(name=self.name,
                         route="/{envId}/servers/{serverId}/",
                         http_method="get",
                         api_level="user")
            status = "running"
            click.echo("Waiting for server %s to suspend.." % server_id)
            while status in ("running", "pending_suspend"):
                data = action.run(**{"serverId": server_id, "hide_output": True,
                                     "envId": kwargs.get('envId')})
                data_json = json.loads(data)
                status = data_json["data"]["status"]
                time.sleep(1)
            click.echo("Server %s has been suspended." % server_id)

        return result


class TerminateServer(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl servers terminate --serverId <ID> --force --nowait"
    post_template = {
        "serverTerminationOptions": {"force": True}
    }

    def get_options(self):
        nowait_hlp = "Do not wait for server to reach 'terminated' state"
        nowait = click.Option(('--nowait', 'nowait'), is_flag=True, required=False, help=nowait_hlp)
        hlp = "It is used to terminate the Server immediately ignoring scalr.system.server_terminate_timeout."
        force_terminate = click.Option(('--force', 'force'), is_flag=True, default=False, help=hlp)
        options = [force_terminate, nowait]
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

    def run(self, *args, **kwargs):
        nowait = kwargs.pop("nowait", False)
        result = super(TerminateServer, self).run(*args, **kwargs)
        if not nowait:
            result_json = json.loads(result)
            server_id = result_json["data"]["id"]
            cls = commands.Action
            action = cls(name=self.name,
                         route="/{envId}/servers/{serverId}/",
                         http_method="get",
                         api_level="user")
            status = "running"
            click.echo("Waiting for server %s to terminate.." % server_id)
            while status in ("running", "pending_terminate"):
                data = action.run(**{"serverId": server_id,
                                     "hide_output": True,
                                     "envId": kwargs.get('envId')})
                data_json = json.loads(data)
                status = data_json["data"]["status"]
                time.sleep(1)
            click.echo("Server %s has been terminated." % server_id)

        return result


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
