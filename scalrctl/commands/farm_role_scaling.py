__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage farmrole scaling'

from scalrctl import commands


name = "farm-role-scaling"
enabled = True


def callback(*args, **kwargs):
    """
    print('in farm_role_scaling module')
    print(args)
    print(kwargs)
    """
    pass


class FarmRoleScaling(commands.SubCommand):
    enabled = True


class FarmRoleScalingList(FarmRoleScaling):
    name = "list"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/"
    method = "get"


class FarmRoleScalingCreate(FarmRoleScaling):
    name = "create"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/"
    method = "post"

class FarmRoleScalingChangeDefaults(FarmRoleScaling):
    name = "change-defaults"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/"
    method = "patch"


class FarmRoleScalingRetrieve(FarmRoleScaling):
    name = "retrieve"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/{metricName}/"
    method = "get"


class FarmRoleScalingDelete(FarmRoleScaling):
    name = "delete"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/{metricName}/"
    method = "delete"


class FarmRoleScalingUpdate(FarmRoleScaling):
    name = "update"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/{metricName}/"
    method = "patch"
