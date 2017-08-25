__author__ = 'Dmitriy Korsakov'
__doc__ = 'Image management'

import copy
from scalrctl import commands
from scalrctl import click


class ChangeImageAttrs(commands.Action):
    prompt_for = ["imageId"]


class RegisterImage(commands.Action):

    def pre(self, *args, **kwargs):
        #XXX: this code does not work yet!
        if 'imageId' not in kwargs:
            kwargs["image"] = click.termui.prompt("Image object JSON")

        return super(RegisterImage, self).pre(*args, **kwargs)


class RetrieveImage(commands.SimplifiedAction):
    prompt_for = ["imageId"]


class ReplaceImageUser(commands.SimplifiedAction):
    epilog = "Example: scalr-ctl images replace --imageID <ID> --newImageID <newID> --deprecateOldImage"

    post_template = {
        "replaceImageRequest": {"deprecateOldImage": False, "newImage": {"id": None}},
    }

    def get_options(self):
        hlp = "The ID of a new image"
        newimageid = click.Option(('--newImageId', 'newimageid'), required=True, help=hlp)
        deprecation_help = "If the value is true Scalr will mark source Image as deprecated."
        deprecate = click.Option(('--deprecateOldImage', 'deprecate'), help=deprecation_help, is_flag=True, default=False)

        options = [newimageid, deprecate]
        options.extend(super(ReplaceImageUser, self).get_options())
        return options

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        post_data = copy.deepcopy(self.post_template)
        newimageid = kwargs.pop("newimageid", None)
        post_data["replaceImageRequest"]["newImage"]["id"] = newimageid
        deprecate = kwargs.pop("deprecate")
        post_data["replaceImageRequest"]["deprecateOldImage"] = deprecate
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(ReplaceImageUser, self).pre(*args, **kv)
        return arguments, kw


class ReplaceImageAccount(commands.SimplifiedAction):
    _default_scope = "account"

    epilog = "Example: scalr-ctl account images replace --imageID <ID> --newImageID <newID> --deprecateOldImage --scope <SCOPE>"

    post_template = {
        "replaceImageRequest": {"deprecateOldImage": False, "scope": None, "newImage": {"id": None}},
    }

    def get_options(self):
        hlp = "The ID of a new image"
        newimageid = click.Option(('--newImageId', 'newimageid'), required=True, help=hlp)
        deprecation_help = "If the value is true Scalr will mark source Image as deprecated."
        deprecate = click.Option(('--deprecateOldImage', 'deprecate'), help=deprecation_help, is_flag=True, default=False)
        scope_help = "Make a replacement for all Roles from the selected scopes. "
        scope_help += "If you choose to make a replacement including lower scope higher scope values will be chosen too"
        scope = click.Option(('--scope', 'scope'), default=self._default_scope, help=scope_help)
        options = [newimageid, deprecate, scope]
        options.extend(super(ReplaceImageAccount, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        post_data = copy.deepcopy(self.post_template)
        scope = kwargs.pop("scope")
        post_data["replaceImageRequest"]["scope"] = scope,
        newimageid = kwargs.pop("newimageid", None)
        post_data["replaceImageRequest"]["newImage"]["id"] = newimageid
        deprecate = kwargs.pop("deprecate")
        post_data["replaceImageRequest"]["deprecateOldImage"] = deprecate
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(ReplaceImageAccount, self).pre(*args, **kv)
        return arguments, kw


class ReplaceImageGlobal(ReplaceImageAccount):
    _default_scope = "scalr"

    epilog = "Example: scalr-ctl global images replace --imageID <ID> --newImageID <newID> --deprecateOldImage --scope <SCOPE>"
