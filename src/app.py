import click


@click.group()
@click.version_option()
def cli():
    """Scalr-tools is a command-line interface to your Scalr account"""


@cli.group("farm")
def farm():
    """Farm manager."""


@farm.command('create')
@click.option('--name', '-n', type=str, required=True, prompt=True, help="New name")
@click.option('--description', '-d', type=str, required=True, prompt=True, help="New description")
def farm_create(name, description):
    """Creates a new farm."""
    click.echo('Created farm %s (%s)' % (name, description))


@farm.command('list')
def farm_list():
    """Returns list of existing farms."""
    click.echo('Displaying list of farms')


@farm.command('update')
@click.option('--farm-id', '-f', type=int, required=True, prompt=True, help="ID of the farm that you want to update.")
@click.option('--name', '-n', type=str, required=True, prompt=True, help="New name")
@click.option('--description', '-d', type=str, required=True, prompt=True, help="New description")
def farm_update(farm_id, name, description):
    """Updates an existing farm"""
    click.echo('Updating farm ID#%s. New name: %s, new description: %s' % (farm_id, name, description))


@farm.command('remove')
@click.option('--farm-id', '-f', type=int, required=True, prompt=True, help="ID of the farm that you want to destroy.")
def farm_remove(farm_id):
    """Destroys a farm"""
    click.echo('farm ID#%s removed.' % farm_id)


@cli.group('farm-role')
def farm_role():
    """FarmRole manager."""


@farm_role.command('list')
@click.option('--farm-id', '-f', type=int, required=True, prompt=True, help="FarmID")
def farm_role_list(farm_id):
    """Returns list of roles in farm."""
    click.echo('Displaying list of roles in farm #%s' % farm_id)


@farm_role.command('remove')
@click.option('--farm-id', '-f', type=int, required=True, prompt=True, help="FarmID")
@click.option('--farm-role-id', type=int, required=True, prompt=True, help="FarmRoleID")
def farm_role_remove(farm_id, farm_role_id):
    """Destroys farm role"""
    click.echo('farm role (ID#%s) removed from farm ID#%s.' % (farm_id, farm_role_id))

