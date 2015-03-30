__author__ = 'shaitanich'

import commands


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
    route = "/{envId}/roles/{roleId}/global-variables/{globalVariableName}"


class RetrieveRoleGlobalVariable(GV):
    name = "retrieve"
    method = "get"
    enabled = True


class UpdateRoleGlobalVariable(GV):
    name = "update"
    method = "patch"
    enabled = True


class DeleteRoleGlobalVariable(GV):
    name = "delete"
    method = "delete"
    enabled = True


class NewRoleGV(GV):
    route = "/{envId}/roles/{roleId}/global-variables/"
    name = "new"
    method = "post"
    enabled = True


class ListRoleGlobalVariables(GV):
    route = "/{envId}/roles/{roleId}/global-variables/"
    name = "update"
    method = "patch"
    enabled = True