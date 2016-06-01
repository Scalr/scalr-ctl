__author__ = 'Dmitriy Korsakov'

import os
import sys
import time
import json
import threading

import yaml
import requests

from scalrctl import click
from scalrctl import defaults
from scalrctl import settings
from scalrctl import commands


successful = False


class UpdateScalrCTL(commands.BaseAction):

    def run(self, *args, **kwargs):
        update()

    def get_description(self):
        return "Fetch new API specification if available."


def is_update_required():
    return not os.path.exists(get_yamlspec_path("user")) \
           or not os.path.exists(get_jsonspec_path("user")) \
           or not os.path.exists(get_yamlspec_path("account")) \
           or not os.path.exists(get_jsonspec_path("account")) \
           or not os.path.exists(get_yamlspec_path("global")) \
           or not os.path.exists(get_jsonspec_path("global"))


def get_spec_url(api_level="user"):
    api_level = api_level or "user"
    return "{0}://{1}/api/{2}.{3}.yml".format(settings.API_SCHEME, settings.API_HOST, api_level, settings.API_VERSION)


def get_trigger_path(api_level="user"):
    fname = ".noupdate.%s" % api_level
    return os.path.join(defaults.CONFIG_DIRECTORY, fname)


def get_yamlspec_path(api_level="user"):
    fname = "%s.yaml" % api_level
    return os.path.join(defaults.CONFIG_DIRECTORY, fname)


def get_jsonspec_path(api_level="user"):
    fname = "%s.json" % api_level
    return os.path.join(defaults.CONFIG_DIRECTORY, fname)


def update_spec(api_level="user"):
    global successful
    paths = []
    text = None

    trigger_path = get_trigger_path(api_level=api_level)
    url = get_spec_url(api_level=api_level)
    yaml_dst = get_yamlspec_path(api_level=api_level)
    json_dst = get_jsonspec_path(api_level=api_level)

    if not os.path.exists(trigger_path):
        r = requests.get(url)

        old = None
        if os.path.exists(yaml_dst):
            with open(yaml_dst, "r") as fp:
                old = fp.read()

        text = r.text

        if text == old:
            successful = True

        elif text:
            with open(yaml_dst, "w") as fp:
                fp.write(text)
            successful = True

    if text or os.path.exists(yaml_dst):
        struct = yaml.load(text or open(yaml_dst).read())
        paths = struct["paths"].keys()
        json.dump(struct, open(json_dst, "w"))

    return paths


def update():
    """
    Downloads yaml spec and converts it to JSON
    Files are stored in configuration directory.
    """
    def spinning_cursor():
        while True:
            for cursor in '|/-\\':
                yield cursor

    def draw_spinner(event):
        spinner = spinning_cursor()
        while not event.isSet():
            sys.stdout.write(spinner.next())
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write('\b')
        sys.stdout.write(' ')
        sys.stdout.flush()

    click.echo("Updating API specifications... ", nl=False)

    e = threading.Event()
    t = threading.Thread(target=draw_spinner, args=(e,))
    t.start()

    try:
        available_routes = {}
        for api_level in ("user", "account", "global"):
            available_routes[api_level] = update_spec(api_level=api_level)
        json.dump(available_routes, open(defaults.ROUTES_PATH, "w"))

    finally:
        e.set()
        t.join()
        if successful:
            click.echo("Done")
        else:
            click.echo("Failed")
