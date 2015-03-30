__author__ = 'shaitanich'

import os

import settings
from view import build_table, build_tree

import click


enabled = False


class SubCommand(object):
    name = None
    route = None
    method = None
    enabled = False


    def pre(self):
        pass


    def post(self):
        pass


    def run(self, *args, **kwargs):
        print
        print "In %s" % type(self)
        if args:
            print args
        if kwargs:
            print kwargs
        print self.method, self.route
        print

        if settings.raw_view:
            test_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'tests'))
            text = open(os.path.join(test_folder, "example.json")).read()
            click.echo(build_tree(text))
        else:
            fields = ["Farm_ID", "Name", "Descriprion"]
            rows = [
                ("1001", "Test_Farm", "First farm"),
                ("1002", "Test_Farm_2", "Second farm"),
            ]
            click.echo(build_table(fields, rows, "Page: 1 of 1", "Total: 1"))