from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
import shutil
import sqlite3
from pydantic import BaseModel
import re
from modules.database.dependencies import get_users_db
from modules.database.config import USERS_DATABASE_PATH
from modules.database.session import users_engine
from utils.logger_config import configure_logger
import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME")

logger = configure_logger()

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={404: {"description": "Not found"}},
)


class BackupResponse(BaseModel):
    message: str
    filename: str
    path: str


@router.post(
    "/backup",
    summary="Créer une sauvegarde de la base SQLite",
    response_model=BackupResponse,
)
async def backup_database():
    """
    Crée une copie du fichier de base de données SQLite dans le dossier `backups/`.
    Avant la copie, on fait un checkpoint WAL pour s'assurer que tout est bien écrit dans le fichier principal.
    """

    prod_db_path = Path(USERS_DATABASE_PATH)

    if not prod_db_path.exists():
        logger.error(f"Base de données SQLite non trouvée à {prod_db_path}.")
        raise HTTPException(
            status_code=404, detail="Base de données SQLite non trouvée."
        )

    try:
        with sqlite3.connect(str(prod_db_path), timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    except Exception as e:
        logger.error(f"Erreur lors du checkpoint WAL : {e}")
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du checkpoint WAL : {e}"
        )

    # Créer le dossier backups s'il n'existe pas
    backups_dir = Path("backups")
    backups_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backups_dir / f"{APP_NAME}_backup_{now}.db"

    try:
        shutil.copy2(prod_db_path, backup_path)
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde : {e}")
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la sauvegarde : {e}"
        )

    logger.info(f"Sauvegarde créée avec succès : {backup_path.name}")

    return {
        "message": "Sauvegarde créée avec succès.",
        "filename": backup_path.name,
        "path": str(backup_path),
    }


@router.get(
    "/monitor/tables",
    summary="Lister les tables et leur nombre de lignes",
    response_model=dict,
)
async def get_table_stats(db: Session = Depends(get_users_db)):
    """
    Pour chaque table de la base, renvoie le nombre de lignes.
    """
    inspector = inspect(users_engine)  # inspecte l'Engine SQLite
    all_tables = inspector.get_table_names()

    stats = []
    for table in all_tables:
        try:
            # NB : SQLite n'a pas de schéma à qualifier, on met le nom brut
            count_res = db.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
        except Exception:
            count_res = None
        stats.append({"table": table, "rows": count_res})

    return {"tables": stats}


@router.get(
    "/monitor/health",
    summary="État de santé basique de la base SQLite",
    response_model=dict,
)
async def get_db_health():
    """
    Retourne des métriques basiques pour SQLite :
    - Résultat de PRAGMA integrity_check
    - Nombre de pages et taille en bytes (via PRAGMA page_count et page_size)
    - Taille du fichier compilé (os.path.getsize)
    - Nombre de pages libres (freelist)
    - Mode journal
    - Niveau de synchronicité
    - Version SQLite
    """
    prod_db_path = Path(USERS_DATABASE_PATH)
    if not prod_db_path.exists():
        raise HTTPException(
            status_code=404, detail="Base de données SQLite non trouvée."
        )

    try:
        with sqlite3.connect(str(prod_db_path), timeout=10) as conn:
            cursor = conn.cursor()

            cursor.execute("PRAGMA journal_mode;")
            journal_mode = cursor.fetchone()[0]

            cursor.execute("PRAGMA integrity_check;")
            integrity_result = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_count;")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size;")
            page_size = cursor.fetchone()[0]

            cursor.execute("PRAGMA freelist_count;")
            freelist_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA synchronous;")
            synchronous_level = cursor.fetchone()[0]
            synchronous = {0: "OFF", 1: "NORMAL", 2: "FULL", 3: "EXTRA"}.get(
                synchronous_level, f"UNKNOWN ({synchronous_level})"
            )

            cursor.execute("SELECT sqlite_version();")
            sqlite_version = cursor.fetchone()[0]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du PRAGMA SQLite : {e}"
        )

    try:
        file_size = prod_db_path.stat().st_size
    except Exception:
        file_size = None

    return {
        "integrity_check": integrity_result,
        "page_count": page_count,
        "page_size": page_size,
        "calculated_size_bytes": page_count * page_size,
        "file_size_bytes": file_size,
        "freelist_count": freelist_count,
        "journal_mode": journal_mode,
        "synchronous": synchronous,
        "sqlite_version": sqlite_version,
    }


@router.get("/backups", summary="Lister les sauvegardes existantes")
async def list_backups():
    backups_dir = Path("backups")
    if not backups_dir.exists():
        return {"backups": []}

    backups = list(backups_dir.glob(f"{APP_NAME}_backup_*.db"))

    backup_list = []
    for backup in backups:
        name = backup.name
        timestamp = None
        try:
            # Chercher pattern date et heure au format YYYYMMDD_HHMMSS dans le nom
            match = re.search(r"(\d{8}_\d{6})", name)
            if match:
                dt_str = match.group(1)  # Exemple: '20250708_154102'
                dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                timestamp = dt.timestamp()
            else:
                raise ValueError("Date pattern not found in backup name")
        except Exception as e:
            logger.error(f"Erreur parsing date dans nom de backup '{name}': {e}")

        backup_list.append(
            {
                "filename": name,
                "created_at": timestamp,
                "size_bytes": backup.stat().st_size,
            }
        )

    # Trier la liste par timestamp décroissant (les plus récents en premier)
    backup_list.sort(key=lambda x: x["created_at"] or 0, reverse=True)

    return {"backups": backup_list}


@router.get("/backup/{filename}")
def download_backup(filename: str):
    file_path = Path("backups") / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    return FileResponse(
        path=str(file_path), filename=filename, media_type="application/octet-stream"
    )


@router.get("/monitor/storage", summary="Espace disque disponible")
async def get_storage_info():
    usage = shutil.disk_usage(".")
    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
    }


@router.delete("/backup/{filename}", summary="Supprimer un fichier de backup")
async def delete_backup(filename: str):
    backups_dir = Path("backups")
    backup_path = backups_dir / filename
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable.")
    try:
        backup_path.unlink()
        return {"message": "Fichier supprimé"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la suppression : {e}"
        )


@router.get("/monitor/logs", summary="Lister les fichiers de logs disponibles")
async def list_logs():
    """
    Liste tous les fichiers de logs classés par dossier (debug, error, warning, app).
    Renvoie aussi leur taille en bytes.
    """
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    log_root = BASE_DIR / "logs"
    log_data = {}

    for subdir in ["app", "debug", "error", "warning"]:
        log_dir = log_root / subdir
        if not log_dir.exists():
            continue
        log_files = list(log_dir.glob("*.log"))
        log_data[subdir] = [
            {"filename": f.name, "path": str(f), "size_bytes": f.stat().st_size}
            for f in log_files
        ]

    return {"logs": log_data}


@router.get(
    "/monitor/logs/{level}",
    summary="Lire le contenu d’un fichier de log (niveau app/debug/error/warning)",
)
async def read_log(level: str, filename: str = Query(None), lines: int = 100):
    valid_levels = {"app", "debug", "error", "warning"}

    if level not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Niveau de log invalide. Choisir parmi : {', '.join(valid_levels)}",
        )

    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    log_dir = BASE_DIR / "logs" / level

    # Si pas de filename, on prend le fichier "par défaut"
    if not filename:
        filename = f"{level}.log"

    log_path = log_dir / filename

    if not log_path.exists() or not log_path.is_file():
        raise HTTPException(status_code=404, detail="Fichier de log non trouvé.")

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return {
                "log_level": level,
                "path": str(log_path),
                "lines": all_lines[-lines:],
            }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la lecture du fichier : {e}"
        )
