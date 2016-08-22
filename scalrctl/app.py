# -*- coding: utf-8 -*-
import json
import os
import pydoc
import sys

import yaml

from scalrctl import click, defaults, settings
from scalrctl.commands import Action
from scalrctl.commands.internal import configure, update

__author__ = 'Dmitriy Korsakov, Sergey Babak'


SCHEME_PATH = os.path.join(os.path.dirname(__file__), 'scheme/scheme.json')


if not os.path.exists(defaults.CONFIG_DIRECTORY):
    os.makedirs(defaults.CONFIG_DIRECTORY)

if os.path.exists(defaults.CONFIG_PATH):
    config_data = yaml.load(open(defaults.CONFIG_PATH, 'r'))
    configure.apply_settings(config_data)

if update.is_update_required():
    update.update()  # [ST-53]


def dummy_run():
    raise click.ClickException("Not implemented in current API version")


class ScalrCLI(click.Group):

    def __init__(self, name=None, commands=None, **attrs):
        if 'scheme' in attrs:
            self.scheme = attrs.pop('scheme')
        else:
            with open(SCHEME_PATH) as fp:
                self.scheme = json.load(fp)
        super(ScalrCLI, self).__init__(name, commands, chain=True, **attrs)

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
        a `Command` object if it exists or returns `ScalrCLI`.
        """

        if name in self.scheme:
            subscheme = self.scheme[name]
        else:
            click.echo('No such command: {}.'.format(name))
            ctx.exit()

        # action level
        if 'route' in subscheme and 'http-method' in subscheme:
            hidden = subscheme.get('hidden', False)
            cls = pydoc.locate(
                subscheme['class']
            ) if 'class' in subscheme else Action
            action = cls(name=name,
                         route=subscheme.get('route'),
                         http_method=subscheme.get('http-method'),
                         api_level=subscheme.get('api_level'))

            try:
                action.validate()
            except AssertionError:
                dummy_help = 'Not implemented in current API version'
                return click.Command(name, params=[], callback=dummy_run,
                                     short_help=dummy_help, hidden=hidden)

            msg = subscheme.get('cmd_descr') or action.get_description()
            options = action.modify_options(action.get_options())
            cmd = click.Command(name, params=options, callback=action.run,
                                short_help=msg, help=msg, hidden=hidden)
            if 'epilog' in subscheme:
                cmd.epilog = subscheme['epilog']
            elif action.epilog:
                cmd.epilog = action.epilog
            return cmd
        else:
            return ScalrCLI(scheme=subscheme,
                            short_help=subscheme.get('group_descr', ''))


@click.command(cls=ScalrCLI)
@click.version_option()
@click.pass_context
@click.option('--key_id', help="API key ID")
@click.option('--secret_key', help="API secret key")
@click.option('--config', help="Path to a custom scalr-ctl configuration file")
def cli(ctx, key_id, secret_key, config, *args, **kvargs):
    """Scalr-ctl is a command-line interface to your Scalr account"""

    service_cmd = any(arg in ('configure', 'update') for arg in sys.argv)

    if key_id:
        settings.API_KEY_ID = str(key_id)

    if secret_key:
        settings.API_SECRET_KEY = str(secret_key)
    elif (settings.API_KEY_ID and settings.API_KEY_ID.strip()
          and not settings.API_SECRET_KEY
          and not service_cmd):  # [ST-21]
        settings.API_SECRET_KEY = str(click.prompt(text='API SECRET KEY',
                                                   hide_input=True))
    if config:
        if os.path.exists(config):
            config_data = yaml.load(open(config, 'r'))
            configure.apply_settings(config_data)
        else:
            msg = 'Configuration file not found: {}'.format(config)
            raise click.ClickException(msg)


if __name__ == '__main__':
    cli()
