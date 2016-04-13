__author__ = 'Dmitriy Korsakov'
__doc__ = 'Image management'

from scalrctl import commands
from scalrctl import click


class ChangeImageAttrs(commands.Action):
    mutable_body_parts = ["name"]
    prompt_for = ["imageId"]


class RegisterImage(commands.Action):

    def pre(self, *args, **kwargs):
        #XXX: this code does not work yet!
        if 'imageId' not in kwargs:
            kwargs["image"] = click.termui.prompt("Image object JSON")
        return args, kwargs


class RetrieveImage(commands.Action):
    prompt_for = ["imageId"]
