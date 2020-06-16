import subprocess
from tchotcho.log import log
from typing import Optional
import pathlib
import attr
import click


@attr.s(auto_attribs=True)
class ProcMsg:
    cmd: str = attr.ib()
    stdout: str = attr.ib()
    stderr: str = attr.ib()
    ok: Optional[bool] = attr.ib()
    code: Optional[int] = attr.ib()


class ShellManager(object):
    def run_cmd(self, cmd, _iter=False):
        log.info("Executing cmd: %s" % " ".join(cmd))

        proc = subprocess.Popen(
            cmd,
            shell=False,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        if not _iter:
            try:
                stdout, stderr = proc.communicate()
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
            except Exception:
                proc.kill()
                proc.wait()
        else:
            stdout = proc.stdout
            stderr = proc.stderr

        returncode = proc.poll()
        ok = None
        if returncode is not None:
            ok = returncode == 0

        log.debug(proc.args)

        pmsg = ProcMsg(cmd, stdout, stderr, ok, returncode)

        if pmsg.ok is not None and not pmsg.ok:
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
            cmd.extend(["-e", f"ssh -o IdentitiesOnly=yes -o StrictHostKeyChecking=no -i {privat_key}"])
        cmd.extend([src, dst])
        pmsg = self.run_cmd(cmd)
        if pmsg.ok:
            summary = " ".join([x for x in pmsg.stdout.split("\n") if x][-2:])
            log.info(f"rsync summary: {summary}")
        return pmsg

    def ssh(self, privat_key, host, command, _iter):
        cmd = [
            "ssh",
            "-i",
            privat_key,
            "-o",
            "ServerAliveInterval=60",
            "-o",
            "ServerAliveCountMax=2",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "IdentitiesOnly=yes",
            host,
            command,
        ]
        pmsg = self.run_cmd(cmd, _iter=_iter)
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
@click.option("--it/--no-it", default=False)
def ssh(privat_key, host, cmd, it):
    pmsg = mgr.ssh(privat_key, host, cmd, it)
    if it:
        for line in pmsg.stdout:
            click.echo(line)
        for line in pmsg.stderr:
            click.echo(line)
    else:
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
