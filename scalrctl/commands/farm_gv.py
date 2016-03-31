__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for farms'


from scalrctl import commands


name = "farm-global-variables"
enabled = True


def callback(*args, **kwargs):
    """
    print('in farm-global-variables module')
    print(args)
    print(kwargs)
    """
    pass


class GV(commands.SubCommand):
    route = "/{envId}/farms/{farmId}/global-variables/{globalVariableName}/"


class DeleteFarmGlobalVariable(GV):
    name = "delete"
    method = "delete"
    enabled = True


class ListFarmGlobalVariables(GV):

    route = "/{envId}/farms/{farmId}/global-variables/"
    name = "list"
    method = "get"
    enabled = True


class NewFarmGV(GV):
    route = "/{envId}/farms/{farmId}/global-variables/"
    name = "create"
    method = "post"
    enabled = True


class RetrieveFarmGlobalVariable(GV):
    name = "retrieve"
    method = "get"
    enabled = True


class UpdateFarmGlobalVariable(GV):
    name = "update"
    method = "patch"
    enabled = True
    #object_reference = "#/definitions/GlobalVariable"
    prompt_for = ["roleId", "globalVariableName"]