import boto3
import click
import colorama
import pandas as pd

import tabulate

from tchotcho.log import log
from tchotcho.config import get_settings

colorama.init()


class KeyManager:
    def __init__(self):
        self.ec2 = boto3.client("ec2")
        self.settings = get_settings()

    def add(self, name, path):
        with open(path, "rb") as f:
            data = f.read()
        resp = self.ec2.import_key_pair(KeyName=name, PublicKeyMaterial=data,)
        ret = False
        if resp["ResponseMetadata"]["HTTPStatusCode"] == 200:
            log.info(f"Succesfully imported key {name} from {path}")
            ret = True
        return ret

    def list(self):
        resp = self.ec2.describe_key_pairs()  # KeyName=name)
        ret = [x for x in resp["KeyPairs"]]
        return ret

    def exists(self, name):
        return name in [x["KeyName"] for x in self.list()]

    def create(self, name):
        ret = False
        if self.exists(name):
            log.error(f"Key {name} already exists!")
            return ret

        log.info(f"Creating key {name}...")
        resp = self.ec2.create_key_pair(KeyName=name)
        key = resp["KeyMaterial"]

        KEY_FILE = self.settings.PROG_HOME / name

        if resp["ResponseMetadata"]["HTTPStatusCode"] == 200:
            with open(KEY_FILE, "w") as f:
                f.write(key)
            log.info(f"Succesfully created key {name} in {KEY_FILE}")
            ret = True
        return ret

    def delete(self, name, ask):
        ret = False
        if not self.exists(name):
            log.error(f"Key {name} does not exist!")
            return ret

        log.info(f"Deleting key {name}...")
        resp = self.ec2.delete_key_pair(KeyName=name)
        if resp["ResponseMetadata"]["HTTPStatusCode"] == 200:
            KEY_FILE = self.settings.PROG_HOME / name
            if KEY_FILE.exists():
                cond = input(f"Delete {KEY_FILE} locally? (yes/no)") if ask else "yes"
                if cond.strip().lower() == "yes":
                    KEY_FILE.unlink()
            log.info(f"Succesfully deleted key {name}!")
            ret = True
        return ret


mgr = None


@click.group()
def key():
    global mgr
    mgr = KeyManager()


@key.command()
@click.option("--name", help="Name of key to highlight")
@click.option("--csv/--no-csv", default=False)
def list(name, csv):
    ret = mgr.list()

    def set_color(val):
        if val == name:
            val = colorama.Back.GREEN + val + colorama.Back.RESET
        return val

    # apply to specific column
    df = pd.DataFrame(ret)
    df = df[["KeyName", "KeyFingerprint"]]
    to_print = df.to_json()

    if not csv:
        df["KeyName"] = df["KeyName"].apply(set_color)
        to_print = tabulate.tabulate(
            df, headers="keys", tablefmt="fancy_grid", showindex="never"
        )
    print(to_print)


@key.command()
@click.option("--name", help="Name of key to create", required=True)
def create(name):
    mgr.create(name)
    click.echo(f"Succesfully created key {name}")


@key.command()
@click.option("--name", help="Name of key to highlight", required=True)
@click.option("--ask/--no-ask", default=True)
def delete(name, ask):
    mgr.delete(name, ask)
    click.echo(f"Succesfully deleted key {name}")


@key.command(name="import")
@click.option("--name", help="Name of key to highlight", required=True)
@click.option(
    "--path",
    help="Path to key file",
    required=True,
    type=click.Path(exists=True, resolve_path=True),
)
def _import(name, path):
    mgr.add(name, path)
    click.echo(f"Succesfully imported key {name}")
