__author__ = 'Dmitriy Korsakov'
__doc__ = 'Supported operating systems'


from scalrctl import commands


name = "os"
enabled = True


def callback(*args, **kwargs):
    """
    print('in account.os module')
    print(args)
    print(kwargs)
    """
    pass


class AccountOSList(commands.SubCommand):
    name = "list"
    route = "/os/"
    method = "get"
    enabled = True


class AccountOSRetrieve(commands.SubCommand):
    name = "retrieve"
    route = "/os/{osId}/"
    method = "get"
    enabled = True
