__author__ = 'Dmitriy Korsakov'
__doc__ = 'Role management'


from scalrctl import commands


class ChangeRoleAttrs(commands.Action):
    prompt_for = ["roleId"]
