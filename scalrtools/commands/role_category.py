__author__ = 'shaitanich'
__doc__ = 'Current Role categories'

from scalrtools import commands


name = "role-category"
enabled = True


def callback(*args, **kwargs):
    """
    print('in role_category module')
    print(args)
    print(kwargs)
    """
    pass


class RoleCategory(commands.SubCommand):
    pass


class RoleCategoryRetrieve(RoleCategory):
    name = "retrieve"
    route = "/{envId}/role-categories/{roleCategoryId}/"
    method = "get"
    enabled = True

class RoleCategoryList(RoleCategory):
    name = "list"
    route = "/{envId}/role-categories/"
    method = "get"
    enabled = True
