__author__ = 'Dmitriy Korsakov'

import os
import sys
import time
import json
import threading

import yaml
import requests

from scalrctl import click
from scalrctl import spec
from scalrctl import defaults

SWAGGER_USER_NOUPDATE_TRIGGER = ".noupdate.user"
SWAGGER_USER_FILE = "user.yaml"
SWAGGER_USER_PATH = os.path.join(defaults.CONFIG_FOLDER, SWAGGER_USER_FILE)
SWAGGER_USER_JSONSPEC_FILE = SWAGGER_USER_FILE.split(".")[0] + ".json"
SWAGGER_USER_JSONSPEC_PATH = os.path.join(defaults.CONFIG_FOLDER, SWAGGER_USER_JSONSPEC_FILE)

SWAGGER_ACCOUNT_NOUPDATE_TRIGGER = ".noupdate.account"
SWAGGER_ACCOUNT_FILE = "account.yaml"
SWAGGER_ACCOUNT_PATH = os.path.join(defaults.CONFIG_FOLDER, SWAGGER_ACCOUNT_FILE)
SWAGGER_ACCOUNT_JSONSPEC_FILE = SWAGGER_ACCOUNT_FILE.split(".")[0] + ".json"
SWAGGER_ACCOUNT_JSONSPEC_PATH = os.path.join(defaults.CONFIG_FOLDER, SWAGGER_ACCOUNT_JSONSPEC_FILE)


def is_update_required():
    return not os.path.exists(SWAGGER_USER_PATH) or not os.path.exists(SWAGGER_USER_JSONSPEC_PATH)


def update():
    """
    Downloads yaml spec and converts it to JSON
    Both files are stored in configuration directory.
    """
    successfull = False
    text = None
    user_trigger_file = os.path.join(defaults.CONFIG_FOLDER, SWAGGER_USER_NOUPDATE_TRIGGER)

    user_url = spec.get_spec_url(api_level="user")
    user_dst = os.path.join(defaults.CONFIG_FOLDER, SWAGGER_USER_FILE)

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
        if user_url and not os.path.exists(user_trigger_file):
            # click.echo("Trying to get new UserAPI Spec from %s" % user_url)
            r = requests.get(user_url)

            old = None

            if os.path.exists(user_dst):
                with open(user_dst, "r") as fp:
                    old = fp.read()

            text = r.text

            if text == old:
                # click.echo("UserAPI Spec is already up-to-date.")
                successfull = True
            elif text:
                with open(user_dst, "w") as fp:
                    fp.write(text)
                # click.echo("UserAPI UserSpec successfully updated.")
                successfull = True

        if text or os.path.exists(user_dst):
            struct = yaml.load(text or open(user_dst).read())
            json.dump(struct, open(SWAGGER_USER_JSONSPEC_PATH, "w"))


        # Fetch AccountAPI spec and convert to JSON
        text = None
        account_trigger_file = os.path.join(defaults.CONFIG_FOLDER, SWAGGER_ACCOUNT_NOUPDATE_TRIGGER)
        account_url = spec.get_spec_url(api_level="account")
        account_dst = os.path.join(defaults.CONFIG_FOLDER, SWAGGER_ACCOUNT_FILE)

        if account_url and not os.path.exists(account_trigger_file):
            # click.echo("Trying to get new AccountAPI Spec from %s" % account_url)
            r = requests.get(account_url)

            old = None

            if os.path.exists(account_dst):
                with open(account_dst, "r") as fp:
                    old = fp.read()

            text = r.text

            if text == old:
                # click.echo("AccountAPI Spec is already up-to-date.")
                successfull = True
            elif text:
                with open(account_dst, "w") as fp:
                    fp.write(text)
                # click.echo("AccountAPI Spec successfully updated.")
                successfull = True

        if text or os.path.exists(account_dst):
            struct = yaml.load(text or open(account_dst).read())
            json.dump(struct, open(SWAGGER_ACCOUNT_JSONSPEC_PATH, "w"))

    finally:
        e.set()
        t.join()
        if successfull:
            click.echo("Done")
        else:
            click.echo("Failed")
