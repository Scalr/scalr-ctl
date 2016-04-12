__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for roles'


from scalrctl import commands


class UpdateRoleGlobalVariable(commands.Action):
    name = "update"
    method = "patch"
    enabled = True
    route = "/{envId}/roles/{roleId}/global-variables/{globalVariableName}/"

    prompt_for = ["roleId", "globalVariableName"]
    #object_reference = "#/definitions/GlobalVariable"
