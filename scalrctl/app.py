__author__ = 'Dmitriy Korsakov'

import os
import json
import pydoc

import yaml

from scalrctl import click
from scalrctl import settings
from scalrctl import defaults
from scalrctl import commands

from scalrctl.commands.internal import update


CMD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'commands'))


def apply_settings(data):
    for key, value in data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)


if not os.path.exists(defaults.CONFIG_DIRECTORY):
    os.makedirs(defaults.CONFIG_DIRECTORY)

if os.path.exists(defaults.CONFIG_PATH):
    apply_settings(yaml.load(open(defaults.CONFIG_PATH, "r")))

if update.is_update_required():
    update.update()  # [ST-53]


def dummy_run():
    raise click.ClickException("Not implemented in current API version")

class ScalrCLI(click.Group):

    def __init__(self, name=None, commands=None, **attrs):
        if not "scheme" in attrs:
            with open(os.path.join(os.path.dirname(__file__), 'scheme/scheme.json')) as fp:
                self.scheme = json.load(fp)
        else:
            self.scheme = attrs.pop("scheme")
        super(ScalrCLI, self).__init__(name, commands, **attrs)

    def list_commands(self, ctx):
        commands = self.scheme.keys()

        if "group_descr" in commands:
            commands.remove("group_descr")

        if "route" in commands and "http-method" in commands:
            return []

        commands.sort()
        return commands

    def get_command(self, ctx, name):
        args = dict(
            callback=lambda: None,
        )

        if name not in self.scheme:

            if ctx.protected_args:
                for level in ctx.protected_args:
                    if level in self.scheme:
                        self.scheme = self.scheme[level]
                    else:
                        ctx.exit()

        if name not in self.scheme:
            click.echo("No such command: %s." % name)
            ctx.exit()

        args["scheme"] = self.scheme[name]

        if "group_descr" in self.scheme[name]:
            args["short_help"] = self.scheme[name]["group_descr"]

        action_level = "route" in self.scheme[name] and "http-method" in self.scheme[name]
        is_service_type_action = action_level and not self.scheme[name]["api_level"]

        if action_level:
            if is_service_type_action:
                route = None
                http_method = None
                api_level = None
            else:
                route = self.scheme[name]["route"]
                http_method = self.scheme[name]["http-method"]
                api_level = self.scheme[name]["api_level"]

            if 'class' in self.scheme[name]:
                cls = pydoc.locate(self.scheme[name]['class'])
            else:
                cls = commands.Action

            action = cls(name=name, route=route, http_method=http_method, api_level=api_level)
            hidden = "hidden" in self.scheme[name] and self.scheme[name]['hidden']

            try:
                action.validate()
            except AssertionError, e:
                dummy_help = "Not implemented in current API version"
                dummy_cmd = click.Command(name, params=[], callback=dummy_run, short_help=dummy_help, hidden=hidden)
                return dummy_cmd

            hlp = action.get_description()
            options = action.modify_options(action.get_options())

            cmd = click.Command(name, params=options, callback=action.run, short_help=hlp, hidden=hidden)
            if action.epilog:
                cmd.epilog = action.epilog
            return cmd

        return ScalrCLI(**args)


@click.command(cls=ScalrCLI)
@click.version_option()
@click.pass_context
@click.option('--key_id', help="API key ID")
@click.option('--secret_key', help="API secret key")
def cli(ctx, key_id, secret_key, *args, **kvargs):
    """Scalr-ctl is a command-line interface to your Scalr account"""

    if key_id:
        settings.API_KEY_ID = str(key_id)

    if secret_key:
        settings.API_SECRET_KEY = str(secret_key)

    elif settings.API_KEY_ID and settings.API_KEY_ID.strip() and not settings.API_SECRET_KEY:  # [ST-21]
        if ctx.invoked_subcommand not in ("configure", "update"):
            raw = click.prompt(text="API SECRET KEY", hide_input=True)
            settings.API_SECRET_KEY = str(raw)


if __name__ == '__main__':
    cli()
