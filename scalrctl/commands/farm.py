__author__ = 'Dmitriy Korsakov'
__doc__ = 'Farm management'


from scalrctl import commands


name = "farm"
enabled = True


def callback(*args, **kwargs):
    """
    print('in farm module')
    print(args)
    print(kwargs)
    """
    pass


class Farm(commands.SubCommand):
    pass


class ListFarms(Farm):
    name = "list"
    route = "/{envId}/farms/"
    method = "get"
    enabled = True


class CreateFarm(Farm):
    name = "create"
    route = "/{envId}/farms/"
    method = "post"
    enabled = True


class RetrieveFarm(Farm):
    name = "retrieve"
    route = "/{envId}/farms/{farmId}/"
    method = "get"
    enabled = True


class ChangeFarmAttrs(Farm):
    name = "change-attributes"
    route = "/{envId}/farms/{farmId}/"
    method = "patch"
    enabled = True


class DeleteFarm(Farm):
    name = "delete"
    route = "/{envId}/farms/{farmId}/"
    method = "delete"
    enabled = True


class LaunchFarm(Farm):
    name = "launch"
    route = "/{envId}/farms/{farmId}/actions/launch/"
    method = "post"
    enabled = True


class TerminateFarm(Farm):
    name = "terminate"
    route = "/{envId}/farms/{farmId}/actions/terminate/"
    method = "post"
    enabled = True