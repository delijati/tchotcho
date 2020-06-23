import colorlog
import logging
import os

LOGGER_NAME = "TT"
LEVEL = getattr(logging, os.getenv("TCHOTCHO_LOG_LEVEL", "INFO"), None)
LEVEL_STR = logging.getLevelName(LEVEL)
if not LEVEL:
    LEVEL = logging.INFO

handler = colorlog.StreamHandler()
lformat = ("[%(log_color)s%(levelname)-.1s%(reset)s] "
           "%(fg_cyan)s%(asctime)s%(reset)s "
           "[%(fg_blue)s%(name)s%(reset)s] %(bold)s%(message)s%(reset)s "
           )
extra = "%(fg_yellow)st=%(threadName)s p=%(process)s {%(filename)s:%(lineno)d}%(reset)s"
if LEVEL_STR == "DEBUG":
    lformat += extra

handler.setFormatter(
    colorlog.ColoredFormatter(lformat, datefmt="%Y-%m-%d %H:%M:%S"),
)

log = colorlog.getLogger(LOGGER_NAME)
log.addHandler(handler)
log.setLevel(LEVEL)
log.info("Logging level: %s" % LEVEL_STR)
