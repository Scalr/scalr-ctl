__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for roles'


from scalrctl import commands


class UpdateRoleGlobalVariable(commands.Action):
    prompt_for = ["roleId", "globalVariableName"]
