__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for roles'


from scalrctl import commands


name = "farm-role-global-variables"
enabled = True


def callback(*args, **kwargs):
    """
    print('in farm-role-global-variables module')
    print(args)
    print(kwargs)
    """
    pass


class GV(commands.SubCommand):
    route = "/{envId}/farm-roles/{farmRoleId}/global-variables/{globalVariableName}/"


class DeleteFarmRoleGlobalVariable(GV):
    name = "delete"
    method = "delete"
    enabled = True


class ListFarmRoleGlobalVariables(GV):
    route = "/{envId}/farm-roles/{farmRoleId}/global-variables/"
    name = "list"
    method = "get"
    enabled = True


class NewFarmRoleGV(GV):
    route = "/{envId}/farm-roles/{farmRoleId}/global-variables/"
    name = "create"
    method = "post"
    enabled = True


class RetrieveFarmRoleGlobalVariable(GV):
    name = "retrieve"
    method = "get"
    enabled = True


class UpdateFarmRoleGlobalVariable(GV):
    name = "update"
    method = "patch"
    enabled = True
    #object_reference = "#/definitions/GlobalVariable"
    prompt_for = ["roleId", "globalVariableName"]