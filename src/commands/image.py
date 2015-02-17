__author__ = 'shaitanich'

import commands

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


class RegisterImage(Image):
    name = "register"
    route = "/{envId}/images/"
    method = "post"
    enabled = True


class ListImages(Image):
    name = "list"
    route = "/{envId}/images/"
    method = "get"
    enabled = True


class ChangeImageAttrs(Image):
    name = "change-attributes"
    route = "/{envId}/images/{imageId}/"
    method = "patch"
    enabled = True


class DeleteImage(Image):
    name = "delete"
    route = "/{envId}/images/{imageId}/"
    method = "delete"
    enabled = True


class CopyImage(Image):
    name = "copy"
    route = "/{envId}/images/{imageId}/actions/copy/"
    method = "get"
    enabled = True
