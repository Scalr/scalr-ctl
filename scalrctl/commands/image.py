__author__ = 'Dmitriy Korsakov'
__doc__ = 'Image management'

import copy
import json
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

        return super(RegisterImage, self).pre(*args, **kwargs)


class RetrieveImage(commands.Action):
    prompt_for = ["imageId"]


class ReplaceImage(commands.Action):

    epilog = "Example: scalr-ctl image replace --imageID <ID> --newImageID <newID> --deprecateOldImage --scope <SCOPE>"

    post_template = {
        "replaceImageRequest": {"scope": None, "newImage": {"id": None}},
    }

    _default_scope = "account"

    def get_options(self):
        hlp = "The ID of a new image"
        newimageid = click.Option(('--newImageId', 'newimageid'), required=True, help=hlp)
        deprecation_help = "If the value is true Scalr will mark source Image as deprecated."
        deprecate = click.Option(('--deprecateOldImage', 'deprecate'), help=deprecation_help, is_flag=True)
        scope_help = "Make a replacement for all Roles from the selected scopes. "
        scope_help += "If you choose to make a replacement including lower scope higher scope values will be chosen too"
        scope = click.Option(('--scope', 'scope'), default=self._default_scope, help=scope_help)

        options = [newimageid, deprecate, scope]
        options.extend(super(ReplaceImage, self).get_options())
        for option in options:
            #if option.name == "interactive":
            if option.name == "stdin":
                options.remove(option)
        return options

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        newimageid = kwargs.pop("newimageid", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["replaceImageRequest"]["newImage"]["id"] = newimageid
        scope = kwargs.pop("scope")
        post_data["replaceImageRequest"]["scope"] = scope,
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(ReplaceImage, self).pre(*args, **kv)
        return arguments, kw

    def post(self, response):
        """
        after request is made
        """

        try:
            obj = json.loads(response)
            if "errors" not in obj:
                #roleid = obj["data"]["role"]["id"]
                imageid = obj["data"]["newImage"]["id"]
                click.echo("New image set: %s." % imageid)
        except:
            pass
        return response


class ReplaceImageGlobal(ReplaceImage):

    _default_scope = "scalr"