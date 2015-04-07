__author__ = 'shaitanich'

from scalrtools import commands


name = "os"
enabled = True


def callback(*args, **kwargs):
    """
    print('in image module')
    print(args)
    print(kwargs)
    """
    pass


class OSList(commands.SubCommand):
    name = "list"
    route = "/os/"
    method = "get"
    enabled = True


class OSRetrieve(commands.SubCommand):
    name = "retrieve"
    route = "/os/{osId}"
    method = "get"
    enabled = True
