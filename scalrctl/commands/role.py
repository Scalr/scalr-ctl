__author__ = 'Dmitriy Korsakov'
__doc__ = 'Role management'


from scalrctl import commands


NAME = "role"
enabled = True


def callback(*args, **kwargs):
    """
    print('in role module')
    print(args)
    print(kwargs)
    """
    pass


class ChangeRoleAttrs(commands.SubCommand):
    name = "change-attributes"
    route = "/{envId}/roles/{roleId}/"
    method = "patch"
    enabled = True

    prompt_for = ["roleId"]



