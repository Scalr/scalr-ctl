__author__ = 'Dmitriy Korsakov'

import os
import shutil


PROGNAME = "scalr-tools"
DEFAULT_CONFIGDIR = "~/.scalr"
AUTOCOMPLETE_FNAME = "path.bash.inc"
AUTOCOMPLETE_CONTENT = "_%s_COMPLETE=source %s" % (PROGNAME.upper().replace("-", "_"), PROGNAME)
AUTOCOMPLETE_PATH = os.path.join(os.path.expanduser(DEFAULT_CONFIGDIR), AUTOCOMPLETE_FNAME)

def main():
    if "nt" == os.name: # Click currently only supports completion for Bash.
        return

    import click

    confirmed = click.confirm("Modify profile to update your $PATH and enable bash completion?", default=True, err=True)

    if confirmed:
        with open(AUTOCOMPLETE_PATH, "w") as fp:
            fp.write(AUTOCOMPLETE_CONTENT)

        bashrc_path = os.path.expanduser("~/.bashrc")
        bashprofile_path = os.path.expanduser("~/.bash_profile")
        startup_path = bashprofile_path if os.path.exists(bashprofile_path) else bashrc_path
        startup_path = click.prompt("Enter path to an rc file to update, or leave blank to use", default=startup_path, err=True)

        backup_path = startup_path + ".backup"
        click.echo("Backing up [%s] to [%s]." % (startup_path, backup_path))
        shutil.copy(startup_path, backup_path)

        source_line = "source '%s'" % AUTOCOMPLETE_PATH
        startupfile_content = open(startup_path, "r").read()
        if AUTOCOMPLETE_PATH not in startupfile_content:
            comment = "# The next line enables bash completion for %s." % PROGNAME
            newline = "" if startupfile_content.endswith("\n") else "\n"
            add = "%s%s\n%s" % (newline, comment, source_line)

            # Handling pip install --user and PATH
            local_binpath = os.path.join(os.path.expanduser("~/.local/bin/"), PROGNAME)
            if os.path.exists(local_binpath):
                add += "\nasias %s=%s" % (PROGNAME, local_binpath)

            with open(startup_path, "a") as afp:
                afp.write(add)

        click.echo("Start a new shell for the changes to take effect.")


if __name__ == '__main__':
    main()