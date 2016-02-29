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
    enabled = True


class ListFarms(Farm):
    name = "list"
    route = "/{envId}/farms/"
    method = "get"


class CreateFarm(Farm):
    name = "create"
    route = "/{envId}/farms/"
    method = "post"


class RetrieveFarm(Farm):
    name = "retrieve"
    route = "/{envId}/farms/{farmId}/"
    method = "get"


class ChangeFarmAttrs(Farm):
    name = "change-attributes"
    route = "/{envId}/farms/{farmId}/"
    method = "patch"


class DeleteFarm(Farm):
    name = "delete"
    route = "/{envId}/farms/{farmId}/"
    method = "delete"


class LaunchFarm(Farm):
    name = "launch"
    route = "/{envId}/farms/{farmId}/actions/launch/"
    method = "post"


class TerminateFarm(Farm):
    name = "terminate"
    route = "/{envId}/farms/{farmId}/actions/terminate/"
    method = "post"


class CloneFarm(Farm):
    name = "clone"
    route = "/{envId}/farms/{farmId}/actions/clone/"
    method = "post"