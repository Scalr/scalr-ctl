__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for servers'


from scalrctl import commands


class UpdateServerGlobalVariable(commands.Action):
    prompt_for = ["serverId", "globalVariableName"]
