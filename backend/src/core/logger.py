import logging
import colorlog
from core.setting import load_setting

color_mapping = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red,bg_white",
}


formatter = colorlog.ColoredFormatter(
    "%(log_color)s[%(levelname)s]%(reset)s: %(name)s:%(funcName)s - %(message)s",
    log_colors=color_mapping,
    reset=True,
)

error = False

level = load_setting().log_level
if level.lower() == "debug":
    level = logging.DEBUG
elif level.lower() == "info":
    level = logging.INFO
elif level.lower() == "warning":
    level = logging.WARNING
elif level.lower() == "error":
    level = logging.ERROR
else:
    error = True
    level = logging.INFO

handler = colorlog.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger("lithium")
logger.setLevel(level)
logger.addHandler(handler)
logger.propagate = False
if error:
    logger.error("Invalid log level in settings, defaulting to INFO")
    logger.info("Valid log levels are: DEBUG, INFO, WARNING, ERROR")
    logger.info("To change the log level, edit the settings.json file")
