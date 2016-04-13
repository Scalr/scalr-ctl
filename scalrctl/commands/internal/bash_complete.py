__author__ = 'Dmitriy Korsakov'

import os
import site
import shutil

from scalrctl import click
from scalrctl import defaults


PROGNAME = "scalr-ctl"
AUTOCOMPLETE_FNAME = "path.bash.inc"
AUTOCOMPLETE_CONTENT = "_%s_COMPLETE=source %s" % (PROGNAME.upper().replace("-", "_"), PROGNAME)
AUTOCOMPLETE_PATH = os.path.join(os.path.expanduser(defaults.CONFIG_DIRECTORY), AUTOCOMPLETE_FNAME)


def setup_bash_complete():
    if "nt" == os.name: # Click currently only supports completion for Bash.
        return

    bashrc_path = os.path.expanduser("~/.bashrc")
    bashprofile_path = os.path.expanduser("~/.bash_profile")
    startup_path = bashprofile_path if os.path.exists(bashprofile_path) else bashrc_path
    startup_path = click.prompt("Enter path to an rc file to update, or leave blank to use", default=startup_path, err=True)
    if not os.path.exists(startup_path):
        click.echo("%s not found." % startup_path)
        return

    startupfile_content = open(startup_path, "r").read()

    if AUTOCOMPLETE_PATH not in startupfile_content:
        confirmed = click.confirm("Modify profile to update your $PATH and enable bash completion?", default=True, err=True)

        if confirmed:
            with open(AUTOCOMPLETE_PATH, "w") as fp:
                fp.write(AUTOCOMPLETE_CONTENT)

            backup_path = startup_path + ".backup"
            click.echo("Backing up [%s] to [%s]." % (startup_path, backup_path))
            shutil.copy(startup_path, backup_path)

            newline = "" if startupfile_content.endswith("\n") else "\n"
            comment = "# The next lines enable bash completion for %s.\n" % PROGNAME
            local_bindir = os.path.expanduser(os.path.join(site.USER_BASE, "bin"))
            local_binpath = os.path.join(local_bindir, PROGNAME)
            source_line = 'eval "$(%s)"\n' % AUTOCOMPLETE_CONTENT

            if os.path.exists(local_binpath):
                msg = "Do you want to add %s to your $PATH?" % local_bindir
                export_confirmed = click.confirm(msg, default=True, err=True)
                if export_confirmed:
                    export_line = "export PATH=$PATH:%s\n" % local_bindir  # [ST-112]
                else:
                    source_line = ''
            else:
                export_line = ''

            add = "%s%s%s%s" % (newline, comment, export_line, source_line)

            if export_line or source_line:
                with open(startup_path, "a") as afp:
                    afp.write(add)

            click.echo("Start a new shell for the changes to take effect.")