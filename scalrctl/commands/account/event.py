__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage events available in the Scalr Account'


from scalrctl import commands


name = "account-level-event"
enabled = True


def callback(*args, **kwargs):
    """
    print('in event module')
    print(args)
    print(kwargs)
    """
    pass


class AccountEvent(commands.SubCommand):
    pass


class AccountListEvents(AccountEvent):
    name = "list"
    route = "/events/"
    method = "get"
    enabled = True


class AccountRetrieveEvent(AccountEvent):
    name = "retrieve"
    route = "/events/{eventId}/"
    method = "get"
    enabled = True


class AccountCreateEvent(AccountEvent):
    name = "create"
    route = "/events/"
    method = "post"
    enabled = True


class AccountChangeEventAttrs(AccountEvent):
    name = "change-attributes"
    route = "/events/{eventId}/"
    method = "patch"
    enabled = True


class AccountDeleteEvent(AccountEvent):
    name = "delete"
    route = "/events/{eventId}/"
    method = "delete"
    enabled = True
