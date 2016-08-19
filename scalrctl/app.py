# -*- coding: utf-8 -*-
import json
import os
import pydoc

import yaml

from scalrctl import click, defaults, settings
from scalrctl.commands import Action
from scalrctl.commands.internal import configure, update

__author__ = 'Dmitriy Korsakov'


SCHEME_PATH = os.path.join(os.path.dirname(__file__), 'scheme/scheme.json')


if not os.path.exists(defaults.CONFIG_DIRECTORY):
    os.makedirs(defaults.CONFIG_DIRECTORY)

if os.path.exists(defaults.CONFIG_PATH):
    configure.apply_settings(yaml.load(open(defaults.CONFIG_PATH, "r")))

if update.is_update_required():
    update.update()  # [ST-53]


def dummy_run():
    raise click.ClickException("Not implemented in current API version")


class ScalrCLI(click.MultiCommand):

    def __init__(self, name=None, commands=None, **attrs):
        if 'scheme' in attrs:
            self.scheme = attrs.pop('scheme')
        else:
            with open(SCHEME_PATH) as fp:
                self.scheme = json.load(fp)

        # enables chain mode for sequential subcommands processing
        attrs['chain'] = True

        super(ScalrCLI, self).__init__(name, commands, **attrs)

    def list_commands(self, ctx):
        """
        Returns a list of subcommand names.
        """

        return [k for k, v in self.scheme.items() if type(v) == dict]

    def get_cmd_groups(self):
        """
        List commands divided into groups.
        """

        groups = {}
        for cmd_name in self.scheme.keys():

            if cmd_name in ('cmd-group', 'group_descr', 'api_level'):
                continue

            if 'cmd-group' in self.scheme[cmd_name]:
                group_name = self.scheme[cmd_name]['cmd-group']
            elif 'api_level' in self.scheme[cmd_name]:
                scope_name = self.scheme[cmd_name]['api_level'].capitalize()
                group_name = '{} Scope operations'.format(scope_name)
            else:
                group_name = 'Other API commands'

            if group_name not in groups:
                groups[group_name] = [cmd_name, ]
            else:
                groups[group_name].append(cmd_name)

        return groups

    def format_commands(self, ctx, formatter):
        sections = {}

        for section_name, section_items in self.get_cmd_groups().items():
            rows = []
            for subcommand in section_items:
                cmd = self.get_command(ctx, subcommand)
                if cmd and not cmd.hidden:
                    rows.append((subcommand, cmd.short_help or ''))
            sections[section_name] = rows

        for name, rows in sections.items():
            rows.sort()
            with formatter.section(name):
                formatter.write_dl(rows)

    def get_command(self, ctx, name):
        """
        Given a context and a command name, this returns
        a :class:`Command` object if it exists or returns `None`.
        """

        args = dict(callback=lambda: None, )

        if name not in self.scheme:
            if ctx.protected_args:
                for level in ctx.protected_args:
                    if level in self.scheme:
                        self.scheme = self.scheme[level]
                    else:
                        ctx.exit()

        if name not in self.scheme:
            click.echo('No such command: {}.'.format(name))
            ctx.exit()

        args['scheme'] = self.scheme[name]

        if 'group_descr' in self.scheme[name]:
            args['short_help'] = self.scheme[name]['group_descr']

        action_level = 'route' in self.scheme[name] and 'http-method' in self.scheme[name]
        is_service_type_action = action_level and not self.scheme[name]['api_level']

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
                cls = Action

            action = cls(name=name,
                         route=route,
                         http_method=http_method,
                         api_level=api_level)
            hidden = "hidden" in self.scheme[name] and self.scheme[name]['hidden']

            try:
                action.validate()
            except AssertionError:
                dummy_help = "Not implemented in current API version"
                dummy_cmd = click.Command(name,
                                          params=[],
                                          callback=dummy_run,
                                          short_help=dummy_help,
                                          hidden=hidden)
                return dummy_cmd

            hlp = self.scheme[name]["cmd_descr"] if "cmd_descr" in self.scheme[name] else action.get_description()
            options = action.modify_options(action.get_options())
            cmd = click.Command(name,
                                params=options,
                                callback=action.run,
                                short_help=hlp,
                                help=hlp,
                                hidden=hidden)
            if "epilog" in self.scheme[name]:
                cmd.epilog = self.scheme[name]["epilog"]
            elif action.epilog:
                cmd.epilog = action.epilog
            return cmd

        return ScalrCLI(**args)


@click.command(cls=ScalrCLI)
@click.version_option()
@click.pass_context
@click.option('--key_id', help="API key ID")
@click.option('--secret_key', help="API secret key")
@click.option('--config', help="Path to a custom scalr-ctl configuration file")
def cli(ctx, key_id, secret_key, config, *args, **kvargs):
    """Scalr-ctl is a command-line interface to your Scalr account"""

    if key_id:
        settings.API_KEY_ID = str(key_id)

    if secret_key:
        settings.API_SECRET_KEY = str(secret_key)

    elif settings.API_KEY_ID and \
            settings.API_KEY_ID.strip() and \
            not settings.API_SECRET_KEY:  # [ST-21]
        if ctx.invoked_subcommand not in ("configure", "update"):
            raw = click.prompt(text="API SECRET KEY", hide_input=True)
            settings.API_SECRET_KEY = str(raw)

    if config:
        if not os.path.exists(config):
            raise click.ClickException("Configuration file not found: {}"
                                       .format(config))
        data = yaml.load(open(config, "r"))
        configure.apply_settings(data)


if __name__ == '__main__':
    cli()


'''

    def get_command(self, ctx, name):
        """
        Given a context and a command name, this returns
        a :class:`Command` object if it exists or returns `None`.
        """

        print ('CTX', ctx, name)
        args = dict(callback=lambda: None,)

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
                cls = Action

            action = cls(name=name, route=route, http_method=http_method, api_level=api_level)
            hidden = "hidden" in self.scheme[name] and self.scheme[name]['hidden']

            try:
                action.validate()
            except AssertionError as e:
                dummy_help = "Not implemented in current API version"
                dummy_cmd = click.Command(name, params=[], callback=dummy_run, short_help=dummy_help, hidden=hidden)
                return dummy_cmd

            hlp = self.scheme[name]["cmd_descr"] if "cmd_descr" in self.scheme[name] else action.get_description()
            options = action.modify_options(action.get_options())
            cmd = click.Command(name, params=options, callback=action.run, short_help=hlp, help=hlp, hidden=hidden)
            if "epilog" in self.scheme[name]:
                cmd.epilog = self.scheme[name]["epilog"]
            elif action.epilog:
                cmd.epilog = action.epilog
            return cmd

        return ScalrCLI(**args)
'''