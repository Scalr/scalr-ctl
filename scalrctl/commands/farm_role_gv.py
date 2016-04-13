__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for farm roles'


from scalrctl import commands


class UpdateFarmRoleGlobalVariable(commands.Action):
    prompt_for = ["roleId", "globalVariableName"]
