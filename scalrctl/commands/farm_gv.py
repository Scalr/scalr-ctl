__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for farms'


from scalrctl import commands


class UpdateFarmGlobalVariable(commands.Action):
    prompt_for = ["roleId", "globalVariableName"]