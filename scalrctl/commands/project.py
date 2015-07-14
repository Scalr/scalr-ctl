__author__ = 'Dmitriy Korsakov'
__doc__ = 'View projects'


from scalrctl import commands


name = "project"
enabled = True


def callback(*args, **kwargs):
    """
    print('in project module')
    print(args)
    print(kwargs)
    """
    pass


class ProjectList(commands.SubCommand):
    name = "list"
    route = "/{envId}/projects/"
    method = "get"
    enabled = True


class CreateProject(commands.SubCommand):
    name = "create"
    route = "/{envId}/projects/"
    method = "post"
    enabled = True


class ProjectRetrieve(commands.SubCommand):
    name = "retrieve"
    route = "/{envId}/projects/{projectId}/"
    method = "get"
    enabled = True
