__author__ = 'Dmitriy Korsakov'
__doc__ = 'Server management'
import copy
import json

from scalrctl import commands
from scalrctl import click


class ExecuteScript(commands.PolledAction):

    epilog = "Example: scalr-ctl scripts execute --serverId <ID> --scriptId <ID> --blocking --timeout 30"

    post_template = {"scriptExecutionRequestObject": {"server": None, "blocking": False, "timeout": None}}

    def get_options(self):
        blocking_hlp = "If it is set Scalr Agent will wait for your Script to finish \
        executing before firing and processing further events."
        blocking = click.Option(('--blocking', 'blocking'), is_flag=True, default=False, help=blocking_hlp)

        server_id_hlp = "Identifier of the Server"
        server_id = click.Option(('--serverId', 'serverId'), required=True, help=server_id_hlp)

        timeout_hlp = "How many secconds should Scalr Agent wait before aborting the execution of this Script."
        timeout = click.Option(('--timeout', 'timeout'), required=False, help=timeout_hlp)

        nowait_hlp = "Do not wait for script execution to finish"
        nowait = click.Option(('--nowait', 'nowait'), is_flag=True, required=False, help=nowait_hlp)

        options = [blocking, server_id, timeout, nowait]
        options.extend(super(ExecuteScript, self).get_options())
        return options

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        blocking = kwargs.pop("blocking", False)
        server_id = kwargs.pop("serverId")
        timeout = kwargs.pop("timeout", False)
        post_data = copy.deepcopy(self.post_template)
        post_data["scriptExecutionRequestObject"]["blocking"] = blocking
        post_data["scriptExecutionRequestObject"]["server"] = server_id
        post_data["scriptExecutionRequestObject"]["timeout"] = timeout
        kv = {"import-data": post_data, "nowait": kwargs.pop("nowait", False)}
        kv.update(kwargs)
        arguments, kw = super(ExecuteScript, self).pre(*args, **kv)
        return arguments, kw

    def run(self, *args, **kwargs):
        nowait = kwargs.pop("nowait", False)
        result = super(ExecuteScript, self).run(*args, **kwargs)
        if not nowait:
            result_json = json.loads(result)
            execution_status_id = result_json["data"]["id"]
            cls = commands.Action
            action = cls(name=self.name,
                         route="/{envId}/script-executions/{scriptExecutionId}/",
                         http_method="get",
                         api_level=self.api_level)
            click.echo("Checking script execution status..")
            self._wait_for_status(poll_dict={'scriptExecutionId': execution_status_id},
                                  action_obj=action,
                                  states_to_wait_for=('finished',), hide_output=False)
            click.echo("Server %s has finished executing script %s [scriptExecutionId %s]." % (
                kwargs.get('serverId'),
                kwargs.get('scriptId'),
                execution_status_id
            ))
        return result


class ExecuteScriptVersion(ExecuteScript):

    epilog = "Example: scalr-ctl script-versions execute \
    --serverId <ID> --scriptId <ID> --scriptVersionNumber <num>--blocking --timeout 30"
