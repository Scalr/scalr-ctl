__author__ = 'Dmitriy Korsakov'
__doc__ = 'Image management'

from scalrctl import commands
from scalrctl import click


class ChangeImageAttrs(commands.Action):
    name = "change-attributes"
    route = "/{envId}/images/{imageId}/"
    method = "patch"
    enabled = True

    mutable_body_parts = ["name"]
    prompt_for = ["imageId"]

    def modify_options(self, options):
        options = super(ChangeImageAttrs, self).modify_options(options)
        return options


class RegisterImage(commands.Action):
    name = "register"
    route = "/{envId}/images/"
    method = "post"
    enabled = True

    def pre(self, *args, **kwargs):
        #XXX: this code does not work yet!
        if 'imageId' not in kwargs:
            kwargs["image"] = click.termui.prompt("Image object JSON")
        return args, kwargs


class RetrieveImage(commands.Action):
    name = "retrieve"
    route = "/{envId}/images/{imageId}/"
    method = "get"
    enabled = True

    prompt_for = ["imageId"]








