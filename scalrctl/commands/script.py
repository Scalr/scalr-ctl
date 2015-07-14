__author__ = 'Dmitriy Korsakov'
__doc__ = 'Script management'


from scalrctl import commands


name = "script"
enabled = True


def callback(*args, **kwargs):
    """
    print('in script module')
    print(args)
    print(kwargs)
    """
    pass


class Script(commands.SubCommand):
    pass


class ListScripts(Script):
    name = "list"
    route = "/{envId}/scripts/"
    method = "get"
    enabled = True


class RetrieveScript(Script):
    name = "retrieve"
    route = "/{envId}/scripts/{scriptId}/"
    method = "get"
    enabled = True


class CreateScript(Script):
    name = "create"
    route = "/{envId}/scripts/"
    method = "post"
    enabled = True


class ChangeScriptAttrs(Script):
    name = "change-attributes"
    route = "/{envId}/scripts/{scriptId}/"
    method = "patch"
    enabled = True


class DeleteScript(Script):
    name = "delete"
    route = "/{envId}/scripts/{scriptId}/"
    method = "delete"
    enabled = True
