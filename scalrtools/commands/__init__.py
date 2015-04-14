__author__ = 'shaitanich'

import json
import click
from scalrtools import settings
from scalrtools import request
from scalrtools.view import build_table, build_tree

enabled = False


class SubCommand(object):
    name = None
    route = None
    method = None
    enabled = False

    @property
    def _basepath_uri(self):
        return settings.spec["basePath"]

    @property
    def _request_template(self):
        return "%s%s" % (self._basepath_uri, self.route)

    def pre(self):
        pass


    def post(self):
        pass


    def run(self, *args, **kwargs):
        uri = self._request_template
        query_data = {}

        if settings.envId and '{envId}' in uri and ('envId' not in kwargs or not kwargs['envId']):
            kwargs['envId'] = settings.envId  # XXX

        if kwargs:
            uri = self._request_template.format(**kwargs)

            for key, value in kwargs.items():
                t = "{%s}" % key
                # filtering in-body and empty params
                if value and t not in self._request_template:
                    query_data[key] = value

        raw_response = request.request(self.method, uri, query_data)

        if settings.view == "raw":
            click.echo(raw_response)

        if raw_response:

            response = json.loads(raw_response)
            data = response["data"]
            text = json.dumps(data)

            if settings.debug_mode:
                click.echo(response["meta"])

            if settings.view == "tree":
                click.echo(build_tree(text))

            elif settings.view == "table":
                fields = ["Farm_ID", "Name", "Descriprion"]
                rows = [
                    ("1001", "Test_Farm", "First farm"),
                    ("1002", "Test_Farm_2", "Second farm"),
                ]
                click.echo(build_table(fields, rows, "Page: 1 of 1", "Total: 1"))
