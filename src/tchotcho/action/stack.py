import boto3
from tchotcho.tropo import create_cloudformation
from tchotcho.util import boto_exception, get_wrapped_waiter
from tchotcho.log import log
import pandas as pd
import click
import colorama

import tabulate

colorama.init()


def waiter_callback(response):
    log.info(response)
    if "Stacks" in response:
        log.info(response["Stacks"])
        if "Outputs" in response["Stacks"][0]:
            df = pd.DataFrame(response["Stacks"][0]["Outputs"])
            to_print = tabulate.tabulate(
                df, headers="keys", tablefmt="fancy_grid", showindex="never"
            )
            print(to_print)
    else:
        log.info(response)


class StackManager(object):
    def __init__(self):
        self.cf = boto3.client("cloudformation")

    def _parse_template(self, template_data):
        self.cf.validate_template(TemplateBody=template_data)
        return template_data

    def stack_exists(self, name):
        stacks = self.cf.list_stacks()["StackSummaries"]
        for stack in stacks:
            if stack["StackStatus"] == "DELETE_COMPLETE":
                continue
            if name == stack["StackName"]:
                return True
        return False

    @boto_exception
    def delete(self, name):
        """Delete a stack if it exists by name """
        log.info("Stack is: %s", name)

        if self.stack_exists(name):
            log.info(f"Deleting stack: {name}...")
            self.cf.delete_stack(StackName=name)
            waiter = get_wrapped_waiter(
                self.cf, "stack_delete_complete", waiter_callback
            )
            waiter.wait(StackName=name)
            log.info(f"Stack {name} deleted")
        else:
            log.error(f"Stack {name} does not exist.")

    @boto_exception
    def create(self, name, template):
        "Create stack"

        template_data = self._parse_template(template)

        params = {
            "StackName": name,
            "TemplateBody": template_data,
            "Capabilities": ["CAPABILITY_IAM"],
        }

        if self.stack_exists(name):
            log.error(f"Stack {name} already exists!")
        else:
            print(f"Creating stack: {name}...")
            self.cf.create_stack(**params)
            waiter = get_wrapped_waiter(
                self.cf, "stack_create_complete", waiter_callback
            )
            waiter.wait(StackName=name)
            log.info(f"Stack {name} created")

    @boto_exception
    def list(self):
        resp = self.cf.describe_stacks()
        return resp


mgr = StackManager()


@click.group()
def stack():
    ...


@stack.command()
@click.option("--name", required=True, help="Name of stack to create && key")
@click.option(
    "--ami",
    required=True,
    help="Name of ami to use",
    default="ami-061aaaac62de85935",
    show_default=True,
)
@click.option("--inst", required=True, help="Name of the instance to use")
@click.option("--security_group", help="Name of the security group to use")
@click.option("--subnet", help="Name of the subnet to use")
@click.option("--price", type=float, help="Name of the instance to use")
@click.option("--size", type=int, help="Size of the disk in GB", default=120)
@click.option("--dry/--no-dry", help="Only print yaml no create", default=False)
def create(name, ami, inst, security_group, subnet, price, size, dry):
    yaml = create_cloudformation(
        name,
        ami,
        inst,
        security_group,
        subnet,
        price,
        size,
        extra_user_data='echo "hello" > /tmp/hello.txt',
    )
    if dry:
        click.echo(yaml)
    else:
        mgr.create(name, yaml)


@stack.command()
@click.option("--name", required=True, help="Name of stack to delete")
def delete(name):
    mgr.delete(name)


@stack.command()
@click.option("--name", help="List stacks by name")
@click.option("--csv/--no-csv", default=False)
def list(name, csv):
    ret = mgr.list()
    stacks = ret.get("Stacks")
    if not stacks:
        click.echo("No stacks found!")
        return

    ret = ret["Stacks"]

    def set_color(val):
        if val == name:
            val = colorama.Back.GREEN + val + colorama.Back.RESET
        return val

    # apply to specific column
    df = pd.DataFrame(ret)
    df = df[["StackName", "StackStatus", "CreationTime", "Capabilities"]]
    to_print = df.to_json()

    if not csv:
        df["StackName"] = df["StackName"].apply(set_color)
        to_print = tabulate.tabulate(
            df, headers="keys", tablefmt="fancy_grid", showindex="never"
        )
    print(to_print)
