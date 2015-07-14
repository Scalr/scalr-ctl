__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage images in roles'


from scalrctl import commands


name = "role-image"
enabled = True


def callback(*args, **kwargs):
    """
    print('in image module')
    print(args)
    print(kwargs)
    """
    pass


class RoleImage(commands.SubCommand):
    pass


class UpdateImage(RoleImage):
    name = "update"
    route = "/{envId}/roles/{roleId}/images/"
    method = "post"
    enabled = True


class ListImages(RoleImage):
    name = "list"
    route = "/{envId}/roles/{roleId}/images/"
    method = "get"
    enabled = True


class ImageDetails(RoleImage):
    name = "retrieve"
    route = "/{envId}/roles/{roleId}/images/{imageId}/"
    method = "get"
    enabled = True


class DeleteImage(RoleImage):
    name = "delete"
    route = "/{envId}/roles/{roleId}/images/{imageId}/"
    method = "delete"
    enabled = True


class ReplaceImage(RoleImage):
    name = "replace"
    route = '/{envId}/roles/{roleId}/images/{imageId}/actions/replace/'
    method = "post"
    enabled = True
