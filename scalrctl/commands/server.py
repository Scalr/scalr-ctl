__author__ = 'Dmitriy Korsakov'
__doc__ = 'Server management'
import copy
import json
import time
from scalrctl import commands
from scalrctl import click


class RebootServer(commands.PolledAction):

    epilog = "Example: scalr-ctl servers reboot --serverId <ID> --hard --nowait"

    post_template = {
        "serverRebootOptions": {"hard": True}
    }

    def get_options(self):
        nowait_hlp = "Do not wait for server to resume after soft reboot"
        nowait = click.Option(('--nowait', 'nowait'), is_flag=True, required=False, help=nowait_hlp)
        hlp = "Reboot type. By default the command requests soft reboot unless this \
        option is present. Beware that some types of the instances do \
        not support soft reboot."
        hard_reboot = click.Option(('--hard', 'hard'), is_flag=True, default=False, help=hlp)
        options = [hard_reboot, nowait]
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

    def run(self, *args, **kwargs):
        nowait = kwargs.pop("nowait", False)
        result = super(RebootServer, self).run(*args, **kwargs)
        result_json = json.loads(result)
        server_id = result_json["data"]["id"]
        if kwargs.get('hard'):
                click.echo("Server %s is undergoing hard reboot." % server_id)
        elif not nowait:
            cls = commands.Action
            action = cls(name=self.name,
                         route="/{envId}/servers/{serverId}/",
                         http_method="get",
                         api_level="user")
            click.echo("Waiting for server %s to resume after soft reboot.." % server_id)
            self._wait_for_status(poll_dict={'serverId': server_id},
                                  action_obj=action,
                                  states_to_wait_for=('rebooting',))
            self._wait_for_status(poll_dict={'serverId': server_id},
                                  action_obj=action,
                                  states_to_wait_for=(None,))
            click.echo("Server %s has finished reboot process." % server_id)
        return result

    def _get_operation_status(self, data_json):
        list_operations =  data_json["data"].get('operations', [])
        if list_operations:
            return list_operations[0]['name']


class ResumeServer(commands.PolledAction):

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
            click.echo("Waiting for server %s to resume.." % server_id)
            self._wait_for_status(poll_dict={'serverId': server_id},
                                  action_obj=action,
                                  states_to_wait_for=('running',))
            click.echo("Server %s resumed." % server_id)
        return result


class SuspendServer(commands.PolledAction):

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
            click.echo("Waiting for server %s to suspend.." % server_id)
            self._wait_for_status(poll_dict={'serverId': server_id},
                                  action_obj=action,
                                  states_to_wait_for=('suspended',))
            click.echo("Server %s has been suspended." % server_id)
        return result


class TerminateServer(commands.PolledAction):

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
            click.echo("Waiting for server %s to terminate.." % server_id)
            self._wait_for_status(poll_dict={'serverId': server_id},
                                  action_obj=action,
                                  states_to_wait_for=('terminated',))
        return result


class LaunchServerAlias(commands.PolledAction):

    epilog = "Example: scalr-ctl servers launch --farmRoleId <ID> --nowait"
    post_template = {
        "serverLaunchRequest": {"farmRole": None}
    }
    _table_columns = [u'operations', u'status', u'cloudServerId', u'cloudLocation', u'launchReason',
                      u'farm.id', u'index', u'hostname', u'farmRole.id', u'privateIp', u'publicIp',
                      u'id', u'instanceType.id', u'launched', u'cloudPlatform']

    def get_options(self):
        nowait_hlp = "Do not wait for server to resume"
        nowait = click.Option(('--nowait', 'nowait'), is_flag=True, required=False, help=nowait_hlp)
        hlp = "Launch a new Server for the specified Farm Role."
        farm_role_id = click.Option(('--farmRoleId', 'farm_role_id'), required=True, help=hlp)
        options = [farm_role_id, nowait]
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

    def run(self, *args, **kwargs):
        nowait = kwargs.pop("nowait", False)
        result = super(LaunchServerAlias, self).run(*args, **kwargs)
        if not nowait:
            result_json = json.loads(result)
            server_id = result_json["data"]["id"]
            cls = commands.Action
            action = cls(name=self.name,
                         route="/{envId}/servers/{serverId}/",
                         http_method="get",
                         api_level="user")
            click.echo("Waiting for server %s to launch and bootstrap.." % server_id)
            self._wait_for_status(poll_dict={'serverId': server_id},
                                  action_obj=action,
                                  states_to_wait_for=('running',))
            click.echo("Server %s has reached 'running' state." % server_id)
        return result


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
