__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for farm roles'


from scalrctl import commands


class UpdateFarmRoleGlobalVariable(commands.Action):
    name = "update"
    method = "patch"
    enabled = True
    route = "/{envId}/farm-roles/{farmRoleId}/global-variables/{globalVariableName}/"

    prompt_for = ["roleId", "globalVariableName"]
    #object_reference = "#/definitions/GlobalVariable"