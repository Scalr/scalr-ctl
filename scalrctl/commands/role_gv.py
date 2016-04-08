__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for roles'


from scalrctl import commands


NAME = "role-global-variables"
enabled = True


def callback(*args, **kwargs):
    """
    print('in role-global-variables module')
    print(args)
    print(kwargs)
    """
    pass


class UpdateRoleGlobalVariable(commands.SubCommand):
    name = "update"
    method = "patch"
    enabled = True
    route = "/{envId}/roles/{roleId}/global-variables/{globalVariableName}/"

    prompt_for = ["roleId", "globalVariableName"]
    #object_reference = "#/definitions/GlobalVariable"
