__author__ = 'Dmitriy Korsakov'
__doc__ = 'Image management'

from scalrctl import commands, settings
import click
import json
import sys
import inspect


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
    mutable_body_parts = ["name"]
    prompt_for = ["imageId"]


    def modify_options(self, options):
        options = super(ChangeImageAttrs, self).modify_options(options)
        return options


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

    def pre(self, *args, **kwargs):
        #XXX: this code does not work yet!
        if 'imageId' not in kwargs:
            kwargs["image"] = click.termui.prompt("Image object JSON")
        return args, kwargs


class RetrieveImage(Image):
    name = "retrieve"
    route = "/{envId}/images/{imageId}/"
    method = "get"
    enabled = True
    prompt_for = ["imageId"]








