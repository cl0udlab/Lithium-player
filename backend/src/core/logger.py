import logging
import colorlog
color_mapping = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red,bg_white"
}


formatter = colorlog.ColoredFormatter(
    "%(log_color)s[%(levelname)s]%(reset)s: %(name)s:%(funcName)s - %(message)s",
    log_colors=color_mapping,
    reset=True
)


handler = colorlog.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger("lithium")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False