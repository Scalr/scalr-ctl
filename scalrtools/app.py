__author__ = 'shaitanich'

import os
import sys
import inspect

import yaml
import click

import commands
import settings


cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'commands'))
config_path = os.path.expanduser(os.environ.get("SCALR_APICLIENT_CONFPATH", "~/.scalr/config.yaml"))

class HelpBuilder(object):
    document = None


    def __init__(self, document):
        self.document = document


    def list_paths(self):
        return self.document["paths"].keys()


    def list_http_methods(self, path):
        l = self.document["paths"][path].keys()
        if "parameters" in l:
            l.remove("parameters")
        return l


    def get_method_description(self, path, method="get"):
        return self.document["paths"][path][method]['description']


    def get_body_type_params(self, path, method="get"):
        params = []
        m = self.document["paths"][path][method]
        if "parameters" in m:
            for parameter in m['parameters']:
                params.append(parameter)
        return params


    def get_path_type_params(self, path):
        params = []
        d = self.document["paths"][path]
        if "parameters" in d:
            for parameter in d['parameters']:
                params.append(parameter)
        return params


    def get_params(self, path, method="get"):
        return self.get_body_type_params(path, method) + self.get_path_type_params(path)


def list_module_filenames():
    files = os.listdir(cmd_folder)
    return [fname for fname in files if fname.endswith('.py') and not fname.startswith("_")]


class MyCLI(click.Group):

    _modules = None

    def __init__(self, name=None, commands=None, **attrs):
        click.Group.__init__(self, name, commands, **attrs)
        self._modules = {}
        self._init()

        self.hb = HelpBuilder(settings.spec)


    def _list_module_objects(self):
        return [module for module in self._modules.values() if module.enabled]


    def _list_subcommands(self, command_name):
        objects = []
        for name, obj in inspect.getmembers(self._modules[command_name]):
            if inspect.isclass(obj) and hasattr(obj, 'enabled') and getattr(obj, 'enabled'):
                subcommand = obj()
                if isinstance(subcommand, commands.SubCommand):
                    objects.append(subcommand)
        return objects


    def _list_options(self, subcommand):
        params = self.hb.get_params(subcommand.route, subcommand.method)
        options = []
        for param in params:
            option = click.Option(("--%s" % param['name'], param['name']), required=param['required'], help=param["description"])
            options.append(option)

        if subcommand.method.upper() == 'GET':
            option = click.Option(("--maxresults", "maxResults"), type=int, required=False, help="Show only first N results. Example: --maxresults=2")
            options.append(option)

        return options


    def _init(self):
        for name in list_module_filenames():
            try:
                if sys.version_info[0] == 2:
                    name = name.encode('ascii', 'replace')
                mod = __import__('scalrtools.commands.' + name[:-3], None, None, ['enabled'])
                if hasattr(mod, "name"):
                    self._modules[mod.name] = mod
            except ImportError:
                raise  # pass


    def list_commands(self, ctx):
        rv = [module.name for module in self._list_module_objects()]
        rv.append("configure")
        rv.sort()
        return rv


    def get_command(self, ctx, name):

        if name == "configure":
            configure_help = "Set configuration options in interactive mode"
            configure_cmd = click.Command("configure", callback=configure, help=configure_help)
            return configure_cmd

        elif name not in self._modules:
            raise click.ClickException("No such command: %s" % name)

        group = click.Group(name, callback=self._modules[name].callback)

        for subcommand in self._list_subcommands(name):
            if subcommand.route in self.hb.list_paths() \
                    and subcommand.method in self.hb.list_http_methods(subcommand.route):
                options = self._list_options(subcommand)

                for option in options:
                    if option.name == "envId" and settings.envId:
                        # settings module can contain envId
                        option.required = False

                help = self.hb.get_method_description(subcommand.route, subcommand.method)
                cmd = click.Command(subcommand.name, params=options, callback=subcommand.run, help=help)
                group.add_command(cmd)

        return group


def configure():
    data = {}

    if os.path.exists(config_path):
        old_data = yaml.load(open(config_path, "r"))
        data.update(old_data)


    for obj in dir(settings):
        if not obj.startswith("__") and type(getattr(settings, obj)) in (int, str):
            data[obj] = str(click.prompt(obj, default=getattr(settings, obj)))

    """
    key_id = str(click.prompt('Please enter API KEY ID:'))
    secret_key = str(click.prompt('Please enter API SECRET KEY:'))
    env_id = str(click.prompt('Please enter EnvironmentID:'))
    new_data = dict(API_KEY_ID=key_id,API_SECRET_KEY=secret_key, envId=env_id)
    data.update(new_data)
    """

    configdir = os.path.dirname(config_path)
    if not os.path.exists(configdir):
        os.makedirs(configdir)

    raw = yaml.dump(data, default_flow_style=False, default_style='')
    with open(config_path, 'w') as fp:
        fp.write(raw)

    click.echo()
    click.echo("New config saved:")
    click.echo()
    click.echo(open(config_path, "r").read())


@click.command(cls=MyCLI)
@click.version_option()
@click.pass_context
@click.option('--key_id', help="API key ID")
@click.option('--secret_key', help="API secret key")
@click.option('--debug/--no-debug', default=False, help="Print debug messages")
@click.option('--raw', 'transformation', is_flag=True, flag_value='raw', default=False, help="Print raw response")
@click.option('--table', 'transformation', is_flag=True, flag_value='table', default=False, help="Print response as a colored table")
@click.option('--tree', 'transformation', is_flag=True, flag_value='tree', default=True, help="Print response as a colored tree")
def cli(ctx, key_id, secret_key, debug, transformation, *args, **kvargs):
    """Scalr-tools is a command-line interface to your Scalr account"""

    if debug:
        settings.debug_mode = debug
        click.echo("Debug mode: %s" % settings.debug_mode)
        click.echo("Key ID: %s" % key_id)

    if os.path.exists(config_path):
        config_data = yaml.load(open(config_path, "r"))
        for key, value in config_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

    if key_id:
        settings.API_KEY_ID = str(key_id)
    if secret_key:
        settings.API_SECRET_KEY = str(secret_key)


    settings.view = transformation


    #print('in outer')
    #print(args)
    #print(kvargs)

    pass


if __name__ == '__main__':
    cli()
