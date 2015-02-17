__author__ = 'shaitanich'

import commands

name = "os"
enabled = True


def callback(*args, **kwargs):
    """
    print('in image module')
    print(args)
    print(kwargs)
    """
    pass


class OS(commands.SubCommand):
    name = "retrieve"
    route = "/os/"
    method = "get"
    enabled = True
