import logging
import os
from logging.config import dictConfig
from pathlib import Path
from django.conf import settings


# from config.settings.base import LOG_DIR
# BASE_DIR = Path(__file__).resolve().parent.parent.parent
# LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
# LOG_DIR = settings.LOG_DIR
LOG_DIR = settings.LOG_DIR

FORMATTERS = {
    "default": {
        "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    },
    "colored": {
        "()": "colorlog.ColoredFormatter",
        "format": "%(log_color)s[%(asctime)s] [%(levelname)s] %(name)s: %(message)s%(reset)s",
        "log_colors": {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        }
    }
}

HANDLERS = {
    "colored-console": {
        "class": "logging.StreamHandler",
        "formatter": "colored",
    },
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
        "data_import":{
            "handlers": ["colored-console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


class SessionLogger:
    """
    Логирование действий пользователя в рамках редактирования сценария расписания.
    Каждый пользователь получает отдельный лог-файл.
    """

    def __init__(self, scenario_id: int, user_id: str):
        self.scenario_id = scenario_id
        self.user_id = user_id
        self.logger_name = f"edit_session.{scenario_id}.{user_id}"

        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(logging.INFO)

        self._ensure_file_handler()

    # Создание логгера и файлов
    def _log_file_path(self) -> Path:
        return LOG_DIR / f"scenario_{self.scenario_id}" / f"user_{self.user_id}.log"

    def _ensure_file_handler(self):
        """
        Создаёт FileHandler, если он ещё не подключён.
        """
        log_path = self._log_file_path()

        # Создаём папки
        os.makedirs(log_path.parent, exist_ok=True)

        # Если этот логгер уже имеет FileHandler — повторно не добавляем
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                return

        handler = logging.FileHandler(log_path, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    # Публичные методы

    def debug(self, msg: str):
        self.logger.debug(msg)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def get_logger(self) -> logging.Logger:
        return self.logger

    # Очистка (опционально)

    def close(self):
        """
        Закрывает FileHandler (можно вызывать после завершения работы).
        """
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    dictConfig(CONFIG)
setup_logging()
