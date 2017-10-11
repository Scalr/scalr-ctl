__author__ = 'Dmitriy Korsakov'
__doc__ = 'Farm management'

import json
import copy

from scalrctl import commands
from scalrctl import click

from scalrctl import request, settings


class FarmTerminate(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl farms terminate --farmId <ID> --force"

    post_template = {
        "terminateFarmRequest": {"force": True}
    }

    def get_options(self):
        hlp = "It is used to terminate the Server immediately ignoring scalr.system.server_terminate_timeout."
        force_terminate = click.Option(('--force', 'force'), is_flag=True, default=False, help=hlp)
        options = [force_terminate, ]
        options.extend(super(FarmTerminate, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        force = kwargs.pop("force", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["terminateFarmRequest"]["force"] = force
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(FarmTerminate, self).pre(*args, **kv)
        return arguments, kw


class FarmLaunch(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl farms launch --farmId <ID>"
    post_template = {}

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kv = {"import-data": {}}
        kv.update(kwargs)
        arguments, kw = super(FarmLaunch, self).pre(*args, **kv)
        return arguments, kw


class FarmClone(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl farms clone --farmId <ID> --name MyNewFarm"
    post_template = {
        "cloneFarmRequest": {"name": ""}
    }

    def get_options(self):
        hlp = "The name of a new Farm."
        hard_terminate = click.Option(('--name', 'name'), required=True, help=hlp)
        options = [hard_terminate, ]
        options.extend(super(FarmClone, self).get_options())
        return options


    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        name = kwargs.pop("name", None)
        post_data = copy.deepcopy(self.post_template)
        post_data["cloneFarmRequest"]["name"] = name
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(FarmClone, self).pre(*args, **kv)
        return arguments, kw


class FarmSuspend(FarmLaunch):

    epilog = "Example: scalr-ctl farms suspend --farmId <ID>"
    post_template = {}


class FarmResume(FarmLaunch):

    epilog = "Example: scalr-ctl farms resume --farmId <ID>"
    post_template = {}


class FarmLock(commands.SimplifiedAction):

    epilog = "Example: scalr-ctl farm lock --farmId <ID> --comment <COMMENT> --unlock-permission <ANYONE|OWNER|TEAM>"

    post_template = {
        "lockFarmRequest": {"lockComment": "", "unlockPermission": "anyone"}
    }

    def get_options(self):
        comment = click.Option(('--lockComment', 'comment'), default="", help="Comment to lock a Farm.")
        hlp = "If you would like to prevent other users unlocking the Farm you should set 'owner' options.\
                  With 'team' options only members of the Farm's Teams can unlock this Farm.\
                  Default value 'anyone' means that anyone with access can unlock this Farm."
        unlock_permission = click.Option((
            '--unlockPermission', 'unlock_permission'),
            default="anyone", show_default=True, help=hlp)
        options = [comment, unlock_permission]
        options.extend(super(FarmLock, self).get_options())
        return options

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        comment = kwargs.pop("comment", None)
        unlock_permission = kwargs.pop("unlock_permission", "anyone")
        post_data = copy.deepcopy(self.post_template)
        post_data["lockFarmRequest"]["lockComment"] = comment
        post_data["lockFarmRequest"]["unlockPermission"] = unlock_permission
        kv = {"import-data": post_data}
        kv.update(kwargs)
        arguments, kw = super(FarmLock, self).pre(*args, **kv)
        return arguments, kw


class FarmCreateFromTemplate(commands.Action):

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kwargs = self._apply_arguments(**kwargs)
        stdin = kwargs.pop('stdin', None)
        kwargs["FarmTemplate"] = self._read_object() if stdin else self._edit_example()
        return args, kwargs

    def run(self, *args, **kwargs):
        """
        Callback for click subcommand.
        """
        hide_output = kwargs.pop('hide_output', False)  # [ST-88]
        args, kwargs = self.pre(*args, **kwargs)

        uri = self._request_template
        payload = {}
        data = {}

        if '{envId}' in uri and not kwargs.get('envId') and settings.envId:
            kwargs['envId'] = settings.envId

        if kwargs:
            # filtering in-body and empty params
            uri = self._request_template.format(**kwargs)

            for key, value in kwargs.items():
                param = '{{{}}}'.format(key)
                if value and (param not in self._request_template):
                    data.update(value)

        if self.dry_run:
            click.echo('{} {} {} {}'.format(self.http_method, uri,
                                            payload, data))
            # returns dummy response
            return json.dumps({'data': {}, 'meta': {}})

        data = json.dumps(data)
        raw_response = request.request(self.http_method, self.api_level,
                                       uri, payload, data)
        response = self.post(raw_response)

        text = self._format_response(response, hidden=hide_output, **kwargs)
        if text is not None:
            click.echo(text)

        return response

    def _edit_example(self):
        commentary = \
            '''# The body must be a valid FarmTemplate object.
#
# Type your FarmTemplate object below this line. The above text will not be sent to the API server.'''
        text = click.edit(commentary)
        if text:
            raw_object = "".join([line for line in text.splitlines()
                                  if not line.startswith("#")]).strip()
        else:
            raw_object = ""
        return json.loads(raw_object)
