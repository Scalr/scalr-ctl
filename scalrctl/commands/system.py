__author__ = 'Dmitriy Korsakov'
__doc__ = 'Supported operating systems'


from scalrctl import commands


name = "os"
enabled = True


def callback(*args, **kwargs):
    """
    print('in os module')
    print(args)
    print(kwargs)
    """
    pass


class OSList(commands.SubCommand):
    name = "list"
    route = "/{envId}/os/"
    method = "get"
    enabled = True


class OSRetrieve(commands.SubCommand):
    name = "retrieve"
    route = "/{envId}/os/{osId}/"
    method = "get"
    enabled = True


