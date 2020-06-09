import os

import boto3
import click
import colorama
import pandas as pd

import tabulate

from tchotcho.log import log
from tchotcho.rsa import RSAFingerprintManager
from tchotcho.config import get_settings

colorama.init()


class KeyManager:
    def __init__(self):
        self.ec2 = boto3.client("ec2")
        self.settings = get_settings()

    def _import(self, name, path):
        ret = False
        with open(path, "rb") as f:
            data = f.read()
        if self.exists(name):
            log.error(f"Key {name} already exists!")
            return ret

        resp = self.ec2.import_key_pair(KeyName=name, PublicKeyMaterial=data)
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
        ret = None
        if self.exists(name):
            log.error(f"Key {name} already exists!")
            return None

        log.info(f"Creating key {name}...")
        resp = self.ec2.create_key_pair(KeyName=name)
        priv_key = resp["KeyMaterial"]

        pub_name = "%s.pub" % name
        PRIVATE_KEY_FILE = self.settings.PROG_HOME / name
        PUBLIC_KEY_FILE = self.settings.PROG_HOME / pub_name

        if resp["ResponseMetadata"]["HTTPStatusCode"] == 200:
            with open(PRIVATE_KEY_FILE, "w") as f:
                f.write(priv_key)
            os.chmod(PRIVATE_KEY_FILE, 0o400)
            log.info(f"Succesfully created private key {name} in {PRIVATE_KEY_FILE}")

            rsamgr = RSAFingerprintManager()
            pub_key = rsamgr.extract_private_to_public(PRIVATE_KEY_FILE)

            with open(PUBLIC_KEY_FILE, "w") as f:
                f.write(pub_key)
            os.chmod(PUBLIC_KEY_FILE, 0o400)
            log.info(f"Succesfully created public key {pub_name} in {PUBLIC_KEY_FILE}")

            ret = (PRIVATE_KEY_FILE, PUBLIC_KEY_FILE)

        return ret

    def delete(self, name, ask):
        ret = False
        if not self.exists(name):
            log.error(f"Key {name} does not exist!")
            return ret

        log.info(f"Deleting key {name}...")
        resp = self.ec2.delete_key_pair(KeyName=name)
        if resp["ResponseMetadata"]["HTTPStatusCode"] == 200:

            pub_name = "%s.pub" % name
            PRIVATE_KEY_FILE = self.settings.PROG_HOME / name
            PUBLIC_KEY_FILE = self.settings.PROG_HOME / pub_name
            for KEY_FILE in (PRIVATE_KEY_FILE, PUBLIC_KEY_FILE):
                if KEY_FILE.exists():
                    cond = input(f"Delete {KEY_FILE} locally? (yes/no): ") if ask else "yes"
                    if cond.strip().lower() == "yes":
                        KEY_FILE.unlink()
                log.info(f"Succesfully deleted key {name}!")
            ret = True
        return ret

    def fingerprint(self, path, passphrase):
        rsamgr = RSAFingerprintManager()
        ret = {
            "public": [rsamgr.get_public(path, passphrase)],
            "private": [rsamgr.get_private(path, passphrase)],
        }
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
    ret = mgr.delete(name, ask)
    if ret:
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
    ret = mgr._import(name, path)
    if ret:
        click.echo(f"Succesfully imported key {name}")


@key.command()
@click.option(
    "--path",
    help="Path to key file",
    required=True,
    type=click.Path(exists=True, resolve_path=True),
)
@click.option("--passphrase", prompt=True, hide_input=True, default="")
@click.option("--csv/--no-csv", default=False)
def fingerprint(path, passphrase, csv):
    ret = mgr.fingerprint(path, passphrase)

    # apply to specific column
    df = pd.DataFrame(ret)
    to_print = df.to_json()

    if not csv:
        to_print = tabulate.tabulate(
            df, headers="keys", tablefmt="fancy_grid", showindex="never"
        )
    print(to_print)
