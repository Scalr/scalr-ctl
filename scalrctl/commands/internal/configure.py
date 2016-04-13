__author__ = 'Dmitriy Korsakov'

import os

import yaml

from scalrctl import click
from scalrctl import defaults
from scalrctl import settings
from scalrctl import commands
from scalrctl.commands.internal import bash_complete, update


class ConfigureScalrCTL(commands.BaseAction):

    def run(self, *args, **kwargs):
        configure(**kwargs)

    def get_description(self):
        return "Set configuration options in interactive mode"

    def get_options(self):
        profile_argument = click.Argument(("profile",), required=False)  # [ST-30]
        return [profile_argument, ]


def configure(profile=None):
    """
    Configure command-line client.
    Creates new profile in configuration directory
    and downloads spec file.
    :param profile: Profile name
    """
    confpath = os.path.join(defaults.CONFIG_DIRECTORY, "%s.yaml" % profile) if profile else defaults.CONFIG_PATH
    data = {}

    if os.path.exists(confpath):
        old_data = yaml.load(open(confpath, "r"))
        data.update(old_data)

    click.echo("Configuring %s:" % confpath)

    for obj in dir(settings):
        if not obj.startswith("__"):
            default_value = getattr(settings, obj)
            if isinstance(default_value, bool):
                data[obj] = click.confirm(obj, default=getattr(settings, obj))
            elif not default_value or type(default_value) in (int, str):
                data[obj] = str(click.prompt(obj, default=getattr(settings, obj))).strip()

    if not os.path.exists(defaults.CONFIG_DIRECTORY):
        os.makedirs(defaults.CONFIG_DIRECTORY)

    raw = yaml.dump(data, default_flow_style=False, default_style='')
    with open(confpath, 'w') as fp:
        fp.write(raw)

    click.echo()
    click.echo("New config saved:")
    click.echo()
    click.echo(open(confpath, "r").read())

    for setting, value in data.items():
        setattr(settings, setting, value)

    update.update()
    bash_complete.setup_bash_complete()