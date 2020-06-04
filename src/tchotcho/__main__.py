from tchotcho.action.key import key as key_group
from tchotcho.action.stack import stack as stack_group
from tchotcho.action.spot import spot as spot_group
from tchotcho.action.info import info as info_group
from tchotcho.action.shell import shell as shell_group
import click


@click.group()
def cli():
    ...


cli.add_command(key_group)
cli.add_command(stack_group)
cli.add_command(spot_group)
cli.add_command(info_group)
cli.add_command(shell_group)
