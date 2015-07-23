__author__ = 'Dmitriy Korsakov'
__doc__ = 'FarmRole management'


from scalrctl import commands


name = "farm-role"
enabled = True


def callback(*args, **kwargs):
    """
    print('in farm-role module')
    print(args)
    print(kwargs)
    """
    pass


class FarmRole(commands.SubCommand):
    pass


class RetrieveFarmRole(FarmRole):
    name = "retrieve"
    route = "/{envId}/farm-roles/{farmRoleId}/"
    method = "get"
    enabled = True


class ListFarmRoles(FarmRole):
    name = "list"
    route = "/{envId}/farms/{farmId}/farm-roles/"
    method = "get"
    enabled = True


class CreateFarmRole(FarmRole):
    name = "create"
    route = "/{envId}/farms/{farmId}/farm-roles/"
    method = "post"
    enabled = True


class ChangeFarmRoleAttrs(FarmRole):
    name = "change-attributes"
    route = "/{envId}/farm-roles/{farmRoleId}/"
    method = "patch"
    enabled = True


class DeleteFarmRole(FarmRole):
    name = "delete"
    route = "/{envId}/farm-roles/{farmRoleId}/"
    method = "delete"
    enabled = True


class RetrievePlacementConfiguration(FarmRole):
    name = "retrieve-placement-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/placement/"
    method = "get"
    enabled = True


class UpdatePlacementConfiguration(FarmRole):
    name = "change-placement-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/placement/"
    method = "patch"
    enabled = True


class RetrieveInstanceConfiguration(FarmRole):
    name = "retrieve-instance-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/instance/"
    method = "get"
    enabled = True


class UpdateInstanceConfiguration(FarmRole):
    name = "change-instance-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/instance/"
    method = "patch"
    enabled = True


class RetrieveScalingConfiguration(FarmRole):
    name = "retrieve-scaling-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/"
    method = "get"
    enabled = True


class UpdateScalingConfiguration(FarmRole):
    name = "change-scaling-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/"
    method = "patch"
    enabled = True