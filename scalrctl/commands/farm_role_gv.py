__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for farm roles'


from scalrctl import commands


NAME = "farm-role-global-variables"
enabled = True


def callback(*args, **kwargs):
    """
    print('in farm-role-global-variables module')
    print(args)
    print(kwargs)
    """
    pass


class UpdateFarmRoleGlobalVariable(commands.SubCommand):
    name = "update"
    method = "patch"
    enabled = True
    route = "/{envId}/farm-roles/{farmRoleId}/global-variables/{globalVariableName}/"

    prompt_for = ["roleId", "globalVariableName"]
    #object_reference = "#/definitions/GlobalVariable"