import structlog
import os
from logma.wech import datlog

LOGGER_NAME = "tchotcho"
LEVEL = os.getenv("TCHOTCHO_LOG_LEVEL", "INFO")
LEVEL_EXTERN = os.getenv("TCHOTCHO_LOG_LEVEL", "ERROR")

config = {
    "loggers": {
        LOGGER_NAME: {"handlers": ["default"], "level": LEVEL, "propagate": False}
    }
}

tty = os.getenv("TCHOTCHO_LOG_TTY", "")
tty_flag = None
if tty:
    tty_flag = tty.lower() in ("an", "on", "true", "1")
# XXX all other loggers are on level ERROR e.g. boto, ...
datlog(level=LEVEL_EXTERN, tty=tty_flag, user_config=config)
log = structlog.get_logger(LOGGER_NAME)
