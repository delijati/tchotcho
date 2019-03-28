from pydantic import BaseSettings

import pathlib

_SETTINGS = None


class Settings(BaseSettings):
    PROG_HOME: pathlib.Path = pathlib.Path("~").expanduser() / ".tchotcho"
    GPU_INFO_FILE: pathlib.Path = PROG_HOME / "gpu_info.json"
    PREFIX: str = "tchotcho"

    # class Config:
    #     env_file = os.environ.get("TCHOTCHO_ENV", ".env")


def set_settings(settings):
    global _SETTINGS

    if not settings.PROG_HOME.exists():
        settings.PROG_HOME.mkdir()

    _SETTINGS = settings
    return _SETTINGS


def get_settings():
    return _SETTINGS


set_settings(Settings())
