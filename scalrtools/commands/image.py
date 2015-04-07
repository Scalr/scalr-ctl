__author__ = 'shaitanich'

from scalrtools import commands


name = "image"
enabled = True


def callback(*args, **kwargs):
    """
    print('in image module')
    print(args)
    print(kwargs)
    """
    pass


class Image(commands.SubCommand):
    pass


class ChangeImageAttrs(Image):
    name = "change-attributes"
    route = "/{envId}/images/{imageId}/"
    method = "patch"
    enabled = True


class CopyImage(Image):
    name = "copy"
    route = "/{envId}/images/{imageId}/actions/copy/"
    method = "post"
    enabled = True


class DeleteImage(Image):
    name = "delete"
    route = "/{envId}/images/{imageId}/"
    method = "delete"
    enabled = True


class ListImages(Image):
    name = "list"
    route = "/{envId}/images/"
    method = "get"
    enabled = True


class RegisterImage(Image):
    name = "register"
    route = "/{envId}/images/"
    method = "post"
    enabled = True


class RetrieveImage(Image):
    name = "retrieve"
    route = "/{envId}/images/{imageId}/"
    method = "get"
    enabled = True








