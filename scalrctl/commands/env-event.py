__author__ = 'Dmitriy Korsakov'
__doc__ =  'Manage events available in the Scalr Environment'


from scalrctl import commands


name = "event"
enabled = True


def callback(*args, **kwargs):
    """
    print('in env-event module')
    print(args)
    print(kwargs)
    """
    pass


class EnvEvent(commands.SubCommand):
    pass


class ListEvents(EnvEvent):
    name = "list"
    route = "/{envId}/events/"
    method = "get"
    enabled = True


class RetrieveEvent(EnvEvent):
    name = "retrieve"
    route = "/{envId}/events/{eventId}/"
    method = "get"
    enabled = True


class CreateEvent(EnvEvent):
    name = "create"
    route = "/{envId}/events/"
    method = "post"
    enabled = True


class ChangeEventAttrs(EnvEvent):
    name = "change-attributes"
    route = "/{envId}/events/{eventId}/"
    method = "patch"
    enabled = True


class DeleteEvent(EnvEvent):
    name = "delete"
    route = "/{envId}/events/{eventId}/"
    method = "delete"
    enabled = True
