""""
Event management
"""
from scalrctl import click
from scalrctl import commands


class Fire(commands.Action):
    """
    It fires the Custom Event on the Server.
    """

    ignored_options = ('stdin',)

    def _get_default_options(self):
        default_options = super(Fire, self)._get_default_options()

        server_id = click.Option(('--serverId', 'serverId'), required=True,
                                 help="Identifier of the Server")
        default_options.append(server_id)
        return default_options

    def pre(self, *args, **kwargs):
        server_id = kwargs.pop('serverId', None)
        import_data = {
            'fireEventRequest': {
                'server': {
                    'id': server_id
                }
            }
        }
        kwargs.update({'import-data': import_data})
        return super(Fire, self).pre(*args, **kwargs)
