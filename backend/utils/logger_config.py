from loguru import logger
import os
import inspect
from pathlib import Path
import warnings
from tqdm import tqdm
from datetime import datetime
import logging

BASE_DIR = Path(__file__).resolve().parent.parent

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

is_windows = os.name == "nt"


class TqdmHandler:
    def write(self, message):
        tqdm.write(message.rstrip())

    def flush(self):
        pass


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Calcule dynamiquement la profondeur pour ignorer les frames de logging et pointer sur le vrai appelant
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        # Journalise avec la profondeur dynamique (pour {name} = module de l'appelant) et les exceptions
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def colored_tqdm(iterable, desc, **kwargs):
    """tqdm avec date/heure/fichier, compatible avec Loguru."""

    def get_now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    initial_now = get_now()
    txt = "ℹ️  INFO"
    frame = inspect.stack()[2]
    module_name = frame.frame.f_globals["__name__"]
    bar_format = (
        f"\033[96m{initial_now}\033[0m"
        f" | \033[94m{module_name}\033[0m"
        f" | \033[97m{txt} : {desc}\033[0m"
        " | \033[95m{n_fmt}/{total_fmt} ({percentage:.0f}%)\033[0m"
        " | {bar}"
    )
    return tqdm(
        iterable, desc=desc, bar_format=bar_format, colour="green", ascii=" #", **kwargs
    )


def configure_logger():
    logger.remove()

    log_root = BASE_DIR / "logs"
    app_log_dir = log_root / "app"
    debug_log_dir = log_root / "debug"
    error_log_dir = log_root / "error"
    warning_log_dir = log_root / "warning"

    for directory in [app_log_dir, debug_log_dir, error_log_dir, warning_log_dir]:
        os.makedirs(directory, exist_ok=True)

    log_format = (
        "\033[96m{time:YYYY-MM-DD HH:mm:ss}\033[0m | "
        "\033[94m{name}\033[0m | "
        "<level>{level.icon}  {level.name}</level> | "
        "\033[95m{message}\033[0m"
    )

    logger.add(TqdmHandler(), level="INFO", format=log_format, colorize=True)

    # Désactiver la rotation sur Windows en raison des problèmes de verrouillage de fichiers lors du renommage
    rotation_app = None if is_windows else "1 week"
    rotation_error = None if is_windows else "500 KB"
    rotation_warning = None if is_windows else "500 KB"
    rotation_debug = None if is_windows else "5 MB"

    logger.add(
        app_log_dir / "app.log",
        rotation=rotation_app,
        retention="1 month",
        level="INFO",
        format=log_format,
        enqueue=True,
    )

    logger.add(
        error_log_dir / "error.log",
        level="ERROR",
        filter=lambda record: record["level"].name == "ERROR",
        rotation=rotation_error,
        retention="10 days",
        format=log_format,
        enqueue=True,
    )

    logger.add(
        warning_log_dir / "warning.log",
        level="WARNING",
        filter=lambda record: record["level"].name == "WARNING",
        rotation=rotation_warning,
        retention="10 days",
        format=log_format,
        enqueue=True,
    )

    logger.add(
        debug_log_dir / "debug.log",
        level="DEBUG",
        filter=lambda record: record["level"].name == "DEBUG",
        rotation=rotation_debug,
        retention="10 days",
        format=log_format,
        enqueue=True,
    )

    # Crée une instance partagée de l'InterceptHandler
    intercept_handler = InterceptHandler()

    # Configure le logger racine
    logging.root.setLevel(logging.INFO)
    logging.root.handlers = [intercept_handler]

    loggers = (
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "uvicorn.server",
        "uvicorn.protocols.http",
        "uvicorn.reloader",
        "fastapi",
        "starlette",
        "apscheduler",
        "apscheduler.scheduler",
        "apscheduler.executors",
        "asyncio",
    )
    for logger_name in loggers:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [intercept_handler]
        logging_logger.propagate = False

    return logger