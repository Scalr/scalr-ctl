__author__ = 'Dmitriy Korsakov'
__doc__ = 'RoleImage management'

import copy
import json
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
        options = [newimageid, ]
        options.extend(super(ReplaceRoleImage, self).get_options())
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

    def post(self, response):
        """
        after request is made
        """
        try:
            obj = json.loads(response)
            if "errors" not in obj:
                roleid = obj["data"]["role"]["id"]
                imageid = obj["data"]["image"]["id"]
                click.echo("Role %s now contains new image %s." % (roleid, imageid))
        except:
            pass
        return response


class CreateRoleImage(commands.Action):

    epilog = "Example: scalr-ctl role-image create --roleID <roleID> --imageID <ID>"

    post_template = {
        "roleImageObject": {"image": {"id": None}, "role": {"id": None}}
    }

    def get_options(self):
        hlp = "The ID of a new image"
        imageid = click.Option(('--imageId', 'imageId'), required=True, help=hlp)
        options = [imageid, ]
        options.extend(super(CreateRoleImage, self).get_options())
        return options

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        imageid = kwargs.get("imageId")
        post_data = copy.deepcopy(self.post_template)
        post_data["roleImageObject"]["image"]["id"] = imageid
        post_data["roleImageObject"]["role"]["id"] = kwargs["roleId"]
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(CreateRoleImage, self).pre(*args, **kv)
        return arguments, kw
