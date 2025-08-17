from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import shutil
from pathlib import Path
import sqlite3
from modules.database.config import USERS_DATABASE_PATH
from utils.logger_config import configure_logger
import atexit
import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME")

logger = configure_logger()

BASE_DIR = Path(__file__).parent
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)
MAX_BACKUPS = 10

def backup_sqlite():
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_path = Path(USERS_DATABASE_PATH)
    backup_path = BACKUP_DIR / f"{APP_NAME}_backup_{now}.db"

    if not db_path.exists():
        logger.info(f"No database found at {db_path}, skipping backup.")
        return

    try:
        # WAL checkpoint to ensure the write-ahead log is flushed
        with sqlite3.connect(str(db_path), timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")

        shutil.copy2(db_path, backup_path)
        logger.info(f"Automatic backup created: {backup_path.name}")
        cleanup_old_backups()
    except Exception as e:
        logger.exception(f"Error during automatic backup: {e}")

def cleanup_old_backups():
    try:
        backups = sorted(BACKUP_DIR.glob(f"{APP_NAME}_backup_*.db"), key=lambda f: f.stat().st_mtime, reverse=True)
        for old_backup in backups[MAX_BACKUPS:]:
            try:
                old_backup.unlink()
                logger.info(f"Old backup deleted: {old_backup.name}")
            except Exception as e:
                logger.error(f"Error deleting backup {old_backup.name}: {e}")
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(backup_sqlite, 'interval', days=1, next_run_time=datetime.now())
    scheduler.start()
    logger.info("Automatic backup scheduler started.")
    atexit.register(lambda: scheduler.shutdown())
