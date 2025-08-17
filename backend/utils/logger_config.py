from loguru import logger
import os
from pathlib import Path
import warnings
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent.parent

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

is_windows = os.name == "nt"


class TqdmHandler:
    def write(self, message):
        tqdm.write(message.rstrip())

    def flush(self):
        pass


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
        "<cyan>{time:YYYY-MM-DD HH:mm:ss}</cyan> | "
        "<blue>{name}</blue> | "
        "<level>{level.icon}  {level.name}</level> | "
        "<magenta>{message}</magenta>"
    )

    logger.add(
        TqdmHandler(),
        level="INFO",
        format=log_format,
        colorize=True
    )

    # Disable rotation on Windows due to file locking issues during rename
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

    return logger
