__author__ = 'Dmitriy Korsakov'
__doc__ = 'Server management'
import copy

from scalrctl import commands
from scalrctl import click


class ExecuteScript(commands.Action):

    epilog = "Example: scalr-ctl script execute --serverId <ID> --scriptId <ID> --blocking --timeout 30"

    post_template = {"scriptExecutionRequestObject": {"server": None, "blocking": False, "timeout": None}}

    def get_options(self):
        blocking_hlp = "If it is set Scalr Agent will wait for your Script to finish \
        executing before firing and processing further events."
        blocking = click.Option(('--blocking', 'blocking'), is_flag=True, default=False, help=blocking_hlp)

        server_id_hlp = "Identifier of the Server"
        server_id = click.Option(('--serverId', 'serverId'), required=True, help=server_id_hlp)

        timeout_hlp = "How many secconds should Scalr Agent wait before aborting the execution of this Script."
        timeout = click.Option(('--timeout', 'timeout'), required=False, help=timeout_hlp)

        options = super(ExecuteScript, self).get_options()
        options += [blocking, server_id, timeout]
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
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(ExecuteScript, self).pre(*args, **kv)
        return arguments, kw


class ExecuteScriptVersion(ExecuteScript):

    epilog = "Example: scalr-ctl script-version execute \
    --serverId <ID> --scriptId <ID> --scriptVersionNumber <num>--blocking --timeout 30"
