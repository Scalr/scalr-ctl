__author__ = 'Dmitriy Korsakov'
__doc__ = 'RoleImage management'

import copy

from scalrctl import commands
from scalrctl import click


class ReplaceRoleImage(commands.Action):

    epilog = "Example: scalr-ctl role-image replace --roleID <roleID> --imageID <ID> --newImageID <newID>"

    post_template = {
        "roleImageObject": {"image": {"id": None}, "role": {"id": None}}
    }

    def get_options(self):
        hlp = "The ID of a new image"
        newimageid = click.Option(('--newImageId', 'newimageid'), required=True, help=hlp)
        options = super(ReplaceRoleImage, self).get_options()
        options.append(newimageid)
        return options

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        newimageid = kwargs.pop("newimageid", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["roleImageObject"]["image"]["id"] = newimageid
        post_data["roleImageObject"]["role"]["id"] = kwargs["roleId"]
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(ReplaceRoleImage, self).pre(*args, **kv)
        return arguments, kw