__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for farms'


from scalrctl import commands


class UpdateFarmGlobalVariable(commands.Action):
    name = "update"
    method = "patch"
    route = "/{envId}/farms/{farmId}/global-variables/{globalVariableName}/"

    prompt_for = ["roleId", "globalVariableName"]
    #object_reference = "#/definitions/GlobalVariable"