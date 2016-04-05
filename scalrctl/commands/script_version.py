__author__ = 'Dmitriy Korsakov'
__doc__ = 'Script Version management'


from scalrctl import commands


NAME = "script-version"
enabled = True


def callback(*args, **kwargs):
    """
    print('in script-version module')
    print(args)
    print(kwargs)
    """
    pass


class ScriptVersion(commands.SubCommand):
    pass


class ListScriptVersions(ScriptVersion):
    name = "list"
    route = "/{envId}/scripts/{scriptId}/script-versions/"
    method = "get"
    enabled = True


class RetrieveScriptVersion(ScriptVersion):
    name = "retrieve"
    route = "/{envId}/scripts/{scriptId}/script-versions/{scriptVersionNumber}/"
    method = "get"
    enabled = True


class CreateScriptVersion(ScriptVersion):
    name = "create"
    route = "/{envId}/scripts/{scriptId}/script-versions/"
    method = "post"
    enabled = True


class ChangeScriptVersionAttrs(ScriptVersion):
    name = "change-attributes"
    route = "/{envId}/scripts/{scriptId}/script-versions/{scriptVersionNumber}/"
    method = "patch"
    enabled = True


class DeleteScriptVersion(ScriptVersion):
    name = "delete"
    route = "/{envId}/scripts/{scriptId}/script-versions/{scriptVersionNumber}/"
    method = "delete"
    enabled = True