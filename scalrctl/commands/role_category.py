__author__ = 'Dmitriy Korsakov'
__doc__ = 'Current Role categories'

from scalrctl import commands


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
    enabled = True


class RoleCategoryList(RoleCategory):
    name = "list"
    route = "/{envId}/role-categories/"
    method = "get"


class RoleCategoryCreate(RoleCategory):
    name = "create"
    route = "/{envId}/role-categories/"
    method = "post"


class RoleCategoryRetrieve(RoleCategory):
    name = "retrieve"
    route = "/{envId}/role-categories/{roleCategoryId}/"
    method = "get"


class RoleCategoryDelete(RoleCategory):
    name = "delete"
    route = "/{envId}/role-categories/{roleCategoryId}/"
    method = "delete"


class RoleCategoryUpdate(RoleCategory):
    name = "update"
    route = "/{envId}/role-categories/{roleCategoryId}/"
    method = "patch"
