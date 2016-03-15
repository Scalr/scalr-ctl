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
    enabled = True


class RetrieveFarmRole(FarmRole):
    name = "retrieve"
    route = "/{envId}/farm-roles/{farmRoleId}/"
    method = "get"


class ListFarmRoles(FarmRole):
    name = "list"
    route = "/{envId}/farms/{farmId}/farm-roles/"
    method = "get"


class CreateFarmRole(FarmRole):
    name = "create"
    route = "/{envId}/farms/{farmId}/farm-roles/"
    method = "post"


class ChangeFarmRoleAttrs(FarmRole):
    name = "change-attributes"
    route = "/{envId}/farm-roles/{farmRoleId}/"
    method = "patch"


class DeleteFarmRole(FarmRole):
    name = "delete"
    route = "/{envId}/farm-roles/{farmRoleId}/"
    method = "delete"


class RetrievePlacementConfiguration(FarmRole):
    name = "retrieve-placement-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/placement/"
    method = "get"


class UpdatePlacementConfiguration(FarmRole):
    name = "change-placement-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/placement/"
    method = "patch"


class RetrieveInstanceConfiguration(FarmRole):
    name = "retrieve-instance-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/instance/"
    method = "get"


class UpdateInstanceConfiguration(FarmRole):
    name = "change-instance-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/instance/"
    method = "patch"


class RetrieveScalingConfiguration(FarmRole):
    name = "retrieve-scaling-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/"
    method = "get"


class UpdateScalingConfiguration(FarmRole):
    name = "change-scaling-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/"
    method = "patch"


class BrownFieldImportServer(FarmRole):
    name = "import-server"
    route = "/{envId}/farm-roles/{farmRoleId}/actions/import-server/"
    #route = "/{envId}/farm-roles/{farmRoleId}/actions/import-server/?cloudServerId=i-0e36d7829d681c05a"
    method = "post"
