__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for roles'


import sys
from scalrctl import commands


name = "role-global-variables"
enabled = True


def callback(*args, **kwargs):
    """
    print('in role-global-variables module')
    print(args)
    print(kwargs)
    """
    pass


class GV(commands.SubCommand):
    route = "/{envId}/roles/{roleId}/global-variables/{globalVariableName}/"


class DeleteRoleGlobalVariable(GV):
    name = "delete"
    method = "delete"
    enabled = True


class ListRoleGlobalVariables(GV):
    route = "/{envId}/roles/{roleId}/global-variables/"
    name = "list"
    method = "get"
    enabled = True


class NewRoleGV(GV):
    route = "/{envId}/roles/{roleId}/global-variables/"
    name = "create"
    method = "post"
    enabled = True


class RetrieveRoleGlobalVariable(GV):
    name = "retrieve"
    method = "get"
    enabled = True


class UpdateRoleGlobalVariable(GV):
    name = "update"
    method = "patch"
    enabled = True
    #object_reference = "#/definitions/GlobalVariable"
    prompt_for = ["roleId", "globalVariableName"]