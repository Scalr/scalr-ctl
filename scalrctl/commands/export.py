__author__ = 'Dmitriy Korsakov'
__doc__ = 'Export Scalr Objects'

import json
import datetime

from scalrctl import settings
from scalrctl import commands
from scalrctl import click

import yaml

NAME = "export"
enabled = True


def callback(*args, **kwargs):
    """
    print('in export module')
    print(args)
    print(kwargs)
    """
    pass


class Export(commands.SubCommand):
    enabled = True

    def run(self, *args, **kwargs):
        kv = kwargs.copy()
        kv['hide_output'] = True
        response = super(Export, self).run(*args, **kv)

        kwargs["envId"] = settings.envId

        uri = self._request_template.format(**kwargs)
        d = {
            "API_VERSION": settings.API_VERSION,
            "envId": settings.envId,
            "date": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "API_HOST": settings.API_HOST,
            "METHOD": self.method,
            "URI": uri,
            "command": NAME,
            "action": self.name,
            "arguments": (args, kwargs)
             }

        try:
            response_json = json.loads(response)
        except ValueError, e:
            if settings.debug_mode:
                raise
            raise click.ClickException(str(e))

        response_json["meta"]["scalrctl"] = d
        dump = yaml.safe_dump(response_json, encoding='utf-8', allow_unicode=True, default_flow_style=False)
        click.echo(dump)


class RetrieveImage(Export):
    name = "image"
    route = "/{envId}/images/{imageId}/"
    method = "get"
    enabled = True
    prompt_for = ["imageId"]