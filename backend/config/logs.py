from logging.config import dictConfig
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

FORMATTERS = {
    "default": {
        "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    },
}

HANDLERS = {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "default",
    },
    "constraint-file": {
        "class": "logging.FileHandler",
        "formatter": "default",
        "filename": f"{LOG_DIR}/constraint-check.log",
        "encoding": "utf-8",
    },
    "sql-file": {
        "class": "logging.FileHandler",
        "formatter": "default",
        "filename": f"{LOG_DIR}/sql.log",
        "encoding": "utf-8",
    },
    "system-file": {
        "class": "logging.FileHandler",
        "formatter": "default",
        "filename": f"{LOG_DIR}/system.log",
        "encoding": "utf-8",
    },
}

CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": FORMATTERS,
    "handlers": HANDLERS,
    "loggers": {
        "constraints": {
            "handlers": ["console", "constraint-file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "cheker": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "schedule": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "sql": {
            "handlers": ["console", "sql-file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "system": {
            "handlers": ["console", "system-file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


def setup_logging():
    dictConfig(CONFIG)
