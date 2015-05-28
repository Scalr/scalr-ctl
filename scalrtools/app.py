__author__ = 'shaitanich'

import os
import sys
import inspect

import yaml
import click
import requests

import commands
import settings
import spec


cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'commands'))
config_folder = os.path.expanduser(os.environ.get("SCALR_APICLIENT_CONFDIR", "~/.scalr"))
config_path = os.path.join(config_folder, "config.yaml")

if os.path.exists(config_path):
    config_data = yaml.load(open(config_path, "r"))
    for key, value in config_data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)


class HelpBuilder(object):
    document = None


    def __init__(self, document):
        #XXX: move methods to spec module
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
        result = self.get_path_type_params(path)
        if method.upper() in ("GET", "DELETE"):
            body_params = self.get_body_type_params(path, method)
            result += body_params
        return result

    def returns_iterable(self, path):
        responces = self.document["paths"][path]["get"]['responses']
        if 200 in responces:
            ok200 = responces[200]
            if 'schema' in ok200:
                schema = ok200['schema']
                if '$ref' in schema:
                    reference = schema['$ref']
                    object_key = reference.split("/")[-1]
                    object_descr = self.document["definitions"][object_key]
                    object_properties = object_descr["properties"]
                    data_structure = object_properties["data"]
                    if "type" in data_structure:
                        responce_type = data_structure["type"]
                        if "array" == responce_type:
                            return True
        return False


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

        debug = click.Option(('--debug/--no-debug', 'debug'), default=False, help="Print debug messages")
        options.append(debug)

        for param in params:
            option = click.Option(("--%s" % param['name'], param['name']), required=param['required'], help=param["description"])
            options.append(option)

        if subcommand.method.upper() == 'GET':
            raw = click.Option(('--raw', 'transformation'), is_flag=True, flag_value='raw', default=False, help="Print raw response")
            table = click.Option(('--table', 'transformation'), is_flag=True, flag_value='table', default=False, help="Print response as a colored table")
            tree = click.Option(('--tree', 'transformation'), is_flag=True, flag_value='tree', default=True, help="Print response as a colored tree")
            nocolor = click.Option(('--nocolor', 'nocolor'), is_flag=True, default=False, help="Use colors")
            options += [raw, table, tree, nocolor]

            if self.hb.returns_iterable(subcommand.route):
                maxrez = click.Option(("--maxresults", "maxResults"), type=int, required=False, help="Maximum number of records. Example: --maxresults=2")
                options.append(maxrez)

                pagenum = click.Option(("--pagenumber", "pageNum"), type=int, required=False, help="Current page number. Example: --pagenumber=3")
                options.append(pagenum)

                filthelp = "Apply filters. Example: type=ebs,size=8. "
                spc = spec.Spec(settings.spec, subcommand.route, subcommand.method)
                if spc.filters:
                    filters = sorted(spc.filters)
                    filthelp += "Available filters: %s." % ", ".join(filters)
                    filters = click.Option(("--filters", "filters"), required=False, help=filthelp)
                    options.append(filters)

                columnshelp = "Filter columns in table view [--table required]. Example: NAME,SIZE,SCOPE. "
                available_columns = spc.get_column_names()
                columnshelp +=  "Available columns: %s." % ", ".join(available_columns)
                columns = click.Option(("--columns", "columns"), required=False, help=columnshelp)
                options.append(columns)

        if subcommand.method.upper() in ('PATCH','POST'):
            stdin_help = "Ask for input instead of opening default text editor"
            stdin = click.Option(("--stdin", "stdin"), is_flag=True, default=False, help=stdin_help)
            options.append(stdin)

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
        rv += ["configure", "update"]
        rv.sort()
        return rv


    def get_command(self, ctx, name):

        if name == "configure":
            configure_help = "Set configuration options in interactive mode"
            configure_cmd = click.Command("configure", callback=configure, help=configure_help)
            return configure_cmd

        elif name == "update":
            update_help = "Fetch new API specification if available."
            update_cmd = click.Command("update", callback=update, help=update_help)
            return update_cmd

        elif name not in self._modules:
            raise click.ClickException("No such command: %s" % name)

        group = click.Group(name, callback=self._modules[name].callback, help=self._modules[name].__doc__)

        for subcommand in self._list_subcommands(name):
            if subcommand.route in self.hb.list_paths() \
                    and subcommand.method in self.hb.list_http_methods(subcommand.route):
                options = self._list_options(subcommand)

                options = subcommand.modify_options(options)

                spc = spec.Spec(settings.spec, subcommand.route, subcommand.method)
                cmd = click.Command(subcommand.name, params=options, callback=subcommand.run, help=spc.description)
                group.add_command(cmd)

        return group


def configure():
    data = {}

    if os.path.exists(config_path):
        old_data = yaml.load(open(config_path, "r"))
        data.update(old_data)


    for obj in dir(settings):
        if not obj.startswith("__"):
            default_value = getattr(settings, obj)
            if isinstance(default_value, bool):
                data[obj] = click.confirm(obj, default=getattr(settings, obj))
            elif not default_value or type(default_value) in (int, str):
                data[obj] = str(click.prompt(obj, default=getattr(settings, obj))).strip()

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

    update()


def update():
    if settings.spec_url:
        click.echo("Trying to get new API Spec from %s" % settings.spec_url)
        r = requests.get(settings.spec_url)
        dst = os.path.join(config_folder, "swagger.yaml")
        old = None
        if os.path.exists(dst):
            with open(dst, "r") as fp:
                old = fp.read()
        if r.text == old:
            click.echo("API Spec is already up-to-date.")
        elif r.text:
            with open(dst, "w") as fp:
                fp.write(r.text)
                click.echo("API Spec successfully updated.")




@click.command(cls=MyCLI)
@click.version_option()
@click.pass_context
@click.option('--key_id', help="API key ID")
@click.option('--secret_key', help="API secret key")
def cli(ctx, key_id, secret_key, *args, **kvargs):
    """Scalr-tools is a command-line interface to your Scalr account"""

    if key_id:
        settings.API_KEY_ID = str(key_id)
    if secret_key:
        settings.API_SECRET_KEY = str(secret_key)


if __name__ == '__main__':
    cli()
