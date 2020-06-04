import subprocess
from tchotcho.log import log
import pathlib
import attr
import click


@attr.s(auto_attribs=True)
class ProcMsg:
    cmd: str
    stdout: str
    stderr: str
    ok: bool
    code: int


class ShellManager(object):
    def to_string(self, std):
        return std.decode("utf-8").strip()

    def run_cmd(self, cmd):
        log.info("Executing cmd: %s" % " ".join(cmd))
        proc = subprocess.run(
            cmd, shell=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        log.debug(proc.args)
        pmsg = ProcMsg(
            cmd,
            self.to_string(proc.stdout),
            self.to_string(proc.stderr),
            proc.returncode == 0,
            proc.returncode,
        )
        if not pmsg.ok:
            log.error("%s returncode: %s stderr: %s" % (cmd[0], pmsg.code, pmsg.stderr))
        else:
            log.info(f"{cmd[0]} ok: {pmsg.ok} returncode: {pmsg.code}")
        return pmsg

    def rsync(self, src, dst, dry=False, privat_key=None):
        if not any([char in src for char in (":", "@")]):
            src = str(pathlib.Path(src).resolve())

        if not any([char in dst for char in (":", "@")]):
            dst = str(pathlib.Path(dst).resolve())
        option = "-avzm"
        option += "n" if dry else ""
        cmd = [
            "rsync",
            option,
            # precalculate file list
            "--no-inc-recursive",
            # get nicer summary
            "--info=progress2",
            "--delete",
            "--exclude",
            ".git",
            "--filter=:- .gitignore",
        ]
        if privat_key:
            cmd.extend(["-e", f"ssh -i {privat_key}"])
        cmd.extend([src, dst])
        pmsg = self.run_cmd(cmd)
        if pmsg.ok:
            summary = " ".join([x for x in pmsg.stdout.split("\n") if x][-2:])
            log.info(f"rsync summary: {summary}")
        return pmsg

    def ssh(self, privat_key, host, command):
        cmd = [
            "ssh",
            "-i",
            privat_key,
            "-o",
            "ServerAliveInterval=60",
            "-o",
            "ServerAliveCountMax=2",
            host,
            command,
        ]
        pmsg = self.run_cmd(cmd)
        if pmsg.ok:
            log.info(f"ssh stdout: {pmsg.stdout}")
        return pmsg


mgr = ShellManager()


@click.group()
def shell():
    ...


@shell.command()
@click.option(
    "--privat-key",
    help="Path to key file",
    required=True,
    type=click.Path(exists=True, resolve_path=True),
)
@click.option("--host", help="Host url e.g.: (user@server)", required=True)
@click.option(
    "--cmd", help="Command to execute via ssh e.g.: (pwd ; ls -l)", required=True
)
def ssh(privat_key, host, cmd):
    pmsg = mgr.ssh(privat_key, host, cmd)
    if pmsg.ok:
        msg = pmsg.stdout
    else:
        msg = pmsg.stderr
    click.echo(msg)


@shell.command()
@click.option("--src", help="Source path", required=True)
@click.option(
    "--dst", help="Destination path e.g.: (/home/... or user@server)", required=True
)
@click.option("--dry/--no-dry", help="Only print yaml no create", default=False)
@click.option(
    "--privat-key",
    help="Path to key file",
    type=click.Path(exists=True, resolve_path=True),
)
def rsync(src, dst, dry, privat_key):
    pmsg = mgr.rsync(src, dst, dry, privat_key)
    if pmsg.ok:
        msg = " ".join([x for x in pmsg.stdout.split("\n") if x][-2:])
    else:
        msg = pmsg.stderr
    click.echo(msg)
