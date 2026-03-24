import logging
from logging.config import dictConfig

LOG_DIR="./logs"

CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "constraint-file": {
        "class": "logging.FileHandler",
        "formatter": "default",
        "filename": f"{LOG_DIR}/constraint-check.log",
        "encoding": "utf-8",
    }
    },

    "loggers": {
        "constraints": {               # ваш основной логгер
            "handlers": ["console", "constraint-file"],
            "level": "DEBUG",
            "propagate": False,
        },
    }
}


def setup_logging():
    dictConfig(CONFIG)