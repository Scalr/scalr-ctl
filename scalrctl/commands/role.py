__author__ = 'Dmitriy Korsakov'
__doc__ = 'Role management'


from scalrctl import commands


class ChangeRoleAttrs(commands.Action):
    name = "change-attributes"
    route = "/{envId}/roles/{roleId}/"
    method = "patch"
    enabled = True

    prompt_for = ["roleId"]



