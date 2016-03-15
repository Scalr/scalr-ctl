__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage cloud credentials available in the Scalr Environment'


from scalrctl import commands


name = "cloud-credentials"
enabled = True


def callback(*args, **kwargs):
    """
    print('in env-event module')
    print(args)
    print(kwargs)
    """
    pass


class CloudCredentials(commands.SubCommand):
    pass


class ListCloudCredentials(CloudCredentials):
    name = "list"
    route = "/{envId}/cloud-credentials/"
    method = "get"
    enabled = True


class RetrieveCloudCredentials(CloudCredentials):
    name = "retrieve"
    route = "/{envId}/cloud-credentials/{cloudCredentialsId}/"
    method = "get"
    enabled = True


class CreateCloudCredentials(CloudCredentials):
    name = "create"
    route = "/{envId}/cloud-credentials/"
    method = "post"
    enabled = True


class UpdateCloudCredentials(CloudCredentials):
    name = "change-attributes"
    route = "/{envId}/cloud-credentials/{cloudCredentialsId}/"
    method = "patch"
    enabled = True


class DeleteCloudCredentials(CloudCredentials):
    name = "delete"
    route = "/{envId}/cloud-credentials/{cloudCredentialsId}/"
    method = "delete"
    enabled = True
