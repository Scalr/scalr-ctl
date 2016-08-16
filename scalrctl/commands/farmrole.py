__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage FarmRoles'

from scalrctl import commands


class LaunchServer(commands.Action):

    post_template = {}

    def pre(self, *args, **kwargs):
        """
        before request is made
        """
        kv = {"import-data": {}}
        kv.update(kwargs)
        arguments, kw = super(LaunchServer, self).pre(*args, **kv)
        return arguments, kw