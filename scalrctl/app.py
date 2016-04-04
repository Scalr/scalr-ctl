__author__ = 'Dmitriy Korsakov'

import os
import sys
import inspect

import yaml

from scalrctl import click
from scalrctl import commands
from scalrctl import settings
from scalrctl import spec
from scalrctl import defaults

from scalrctl.commands.internal import configure, update


CMD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'commands'))


class HelpBuilder(object):
    document = None

    def __init__(self, document):
        #XXX: move methods to spec module
        self.document = document

    def list_paths(self):
        return list(self.document["paths"])

    def list_http_methods(self, path):
        l = list(self.document["paths"][path])
        if "parameters" in l:
            l.remove("parameters")
        return l

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
        if '200' in responces:
            ok200 = responces['200']
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


class MyCLI(click.Group):

    _modules = None

    def __init__(self, name=None, commands=None, **attrs):
        super(MyCLI, self).__init__(name, commands, **attrs)
        self._modules = {}
        self._init()
        self.metaspec = spec.MetaSpec.lookup()


    def get_help_builder(self, api_level="user"):
        spec_dict = self.metaspec._get_spec_dict(api_level=api_level)
        return HelpBuilder(spec_dict)


    def _list_module_objects(self):
        objects = [module for module in self._modules.values() if module.enabled]
        return objects


    def _list_subcommands(self, command_name):
        objects = []
        for name, obj in inspect.getmembers(self._modules[command_name]):
            if inspect.isclass(obj) and hasattr(obj, 'enabled') and getattr(obj, 'enabled'):
                subcommand = obj()
                if isinstance(subcommand, commands.SubCommand):
                    objects.append(subcommand)
        return objects


    def _list_options(self, route, method, subcommand_name, api_level="user"):  #XXX: subcommand_name
        help_builder = self.get_help_builder(api_level=api_level)
        params = help_builder.get_params(route, method)
        options = []

        debug = click.Option(('--debug/--no-debug', 'debug'), default=False, help="Print debug messages")
        options.append(debug)

        for param in params:
            option = click.Option(("--%s" % param['name'], param['name']), required=param['required'], help=param["description"])
            options.append(option)

        if method.upper() == 'GET':
            raw = click.Option(('--raw', 'transformation'), is_flag=True, flag_value='raw', default=False, help="Print raw response")
            tree = click.Option(('--tree', 'transformation'), is_flag=True, flag_value='tree', default=True, help="Print response as a colored tree")
            nocolor = click.Option(('--nocolor', 'nocolor'), is_flag=True, default=False, help="Use colors")
            options += [raw, tree, nocolor]

            if subcommand_name not in ("get", "retrieve"):  # [ST-54] [ST-102]
                table = click.Option(('--table', 'transformation'), is_flag=True, flag_value='table', default=False, help="Print response as a colored table")
                options.append(table)
            else:
                export = click.Option(('--export', 'export'), required=False, type=click.Path(), help="Export Scalr Object to JSON file")  # [ST-88]
                options.append(export)

            if help_builder.returns_iterable(route):
                maxrez = click.Option(("--maxresults", "maxResults"), type=int, required=False, help="Maximum number of records. Example: --maxresults=2")
                options.append(maxrez)

                pagenum = click.Option(("--pagenumber", "pageNum"), type=int, required=False, help="Current page number. Example: --pagenumber=3")
                options.append(pagenum)

                filthelp = "Apply filters. Example: type=ebs,size=8. "
                spc = spec.Spec(spec.get_raw_spec(api_level=api_level), route, method)
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

        if method.upper() in ('PATCH','POST'):
            stdin_help = "Ask for input instead of opening default text editor"
            stdin = click.Option(("--stdin", "stdin"), is_flag=True, default=False, help=stdin_help)
            options.append(stdin)

            import_help = "Import object from file"
            from_file = click.Option(("--import", "from_file"), required=False, type=click.Path(), help=import_help)
            options.append(from_file)


        return options


    def _init(self):
        files = os.listdir(CMD_FOLDER)
        list_module_filenames = [fname for fname in files if fname.endswith('.py') and not fname.startswith("_")]

        for name in list_module_filenames:
            try:
                if sys.version_info[0] == 2:
                    name = name.encode('ascii', 'replace')
                mod = __import__('scalrctl.commands.' + name[:-3], None, None, ['enabled'])
                if hasattr(mod, "name"):
                    self._modules[mod.name] = mod
            except ImportError:
                raise  # pass


    def list_commands(self, ctx):
        rv = [module.name for module in self._list_module_objects()]
        rv += ["configure", "update", "account"]
        rv.sort()
        return rv


    def get_command(self, ctx, name):

        if name == "account":
            account_help = "All AccountAPI commands"  # TODO: HelpStr
            account_group = click.Group("account", callback=lambda: None, help=account_help)

            for command_name in self.metaspec._list_cmd_aliases(api_level="account"):
                command_descr = self.metaspec._get_cmd_descr(command_name=command_name, api_level="account")
                grp = click.Group(command_name, callback=lambda: None, help=command_descr)

                for subcommand_name in self.metaspec._list_subcmd_aliases(command_name=command_name, api_level="account"):

                    route = self.metaspec.get_route(command_name, subcommand_name, api_level="account")
                    method = self.metaspec.get_http_method(command_name, subcommand_name, api_level="account")
                    subcommand = commands.SubCommand()
                    subcommand.name = subcommand_name
                    subcommand.route = route
                    subcommand.method = method
                    subcommand.api_level = "account"
                    options = self._list_options(route, method, subcommand_name, api_level="account")
                    options = subcommand.modify_options(options)
                    acc_spec = spec.Spec(spec.get_raw_spec(api_level="account"), route, method)
                    subcommand_descr = acc_spec.description
                    cmd = click.Command(subcommand.name, params=options, callback=subcommand.run, short_help=subcommand_descr)

                    if subcommand_name == "retrieve":  # [ST-102]
                        new_cmd = click.Command("get", params=options, callback=subcommand.run, short_help=subcommand_descr)
                        grp.add_command(new_cmd)
                        cmd.hidden = True
                    elif subcommand_name == "change-attributes":  # [ST-104]
                        new_cmd = click.Command("update", params=options, callback=subcommand.run, short_help=subcommand_descr)
                        grp.add_command(new_cmd)
                        cmd.hidden = True

                    grp.add_command(cmd)

                account_group.add_command(grp)
            return account_group

        elif name == "configure":
            configure_help = "Set configuration options in interactive mode"
            profile_argument = click.Argument(("profile",), required=False)  # [ST-30]
            configure_cmd = click.Command("configure", callback=configure.configure, help=configure_help, params=[profile_argument,])
            return configure_cmd

        elif name == "update":
            update_help = "Fetch new API specification if available."
            update_cmd = click.Command("update", callback=update.update, help=update_help)
            return update_cmd

        elif name not in self._modules:
            raise click.ClickException("No such command: %s" % name)

        group = click.Group(name, callback=self._modules[name].callback, help=self._modules[name].__doc__)

        hb = self.get_help_builder(api_level="user")
        subcommands = self._list_subcommands(name)
        routes = hb.list_paths()
        for subcommand in subcommands:
            if subcommand.route in routes \
                    and subcommand.method in hb.list_http_methods(subcommand.route):
                options = self._list_options(route=subcommand.route, method=subcommand.method, subcommand_name=subcommand.name, api_level="user")

                options = subcommand.modify_options(options)

                spc = spec.Spec(spec.get_raw_spec(api_level="user"), subcommand.route, subcommand.method)
                cmd = click.Command(subcommand.name, params=options, callback=subcommand.run, short_help=spc.description)

                if subcommand.name == "retrieve":  # [ST-102]
                    new_cmd = click.Command("get", params=options, callback=subcommand.run, short_help=spc.description)
                    group.add_command(new_cmd)
                    cmd.hidden = True
                elif subcommand.name == "change-attributes":  # [ST-104]
                    new_cmd = click.Command("update", params=options, callback=subcommand.run, short_help=spc.description)
                    group.add_command(new_cmd)
                    cmd.hidden = True

                group.add_command(cmd)
        return group

def account():
    # debug code
    pass

def apply_settings(data):
    for key, value in data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)


if not os.path.exists(defaults.CONFIG_FOLDER):
    os.makedirs(defaults.CONFIG_FOLDER)

if os.path.exists(defaults.CONFIG_PATH):
    apply_settings(yaml.load(open(defaults.CONFIG_PATH, "r")))

if update.is_update_required():
    update.update()  # [ST-53]


@click.command(cls=MyCLI)
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
