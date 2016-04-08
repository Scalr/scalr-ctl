__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage global variables for farms'


from scalrctl import commands


NAME = "farm-global-variables"
enabled = True


def callback(*args, **kwargs):
    """
    print('in farm-global-variables module')
    print(args)
    print(kwargs)
    """
    pass


class UpdateFarmGlobalVariable(commands.SubCommand):
    name = "update"
    method = "patch"
    enabled = True
    route = "/{envId}/farms/{farmId}/global-variables/{globalVariableName}/"

    prompt_for = ["roleId", "globalVariableName"]
    #object_reference = "#/definitions/GlobalVariable"