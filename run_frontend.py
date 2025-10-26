import os
from dotenv import load_dotenv
import subprocess
import threading
from backend.utils.logger_config import configure_logger

logger = configure_logger()

load_dotenv()

PORT_BACK = os.getenv("PORT_BACK")
APP_NAME = os.getenv("APP_NAME")
PORT_FRONT = os.getenv("PORT_FRONT")
ENV = os.getenv("ENV")
PRINTFUL = os.getenv("PRINTFUL")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")

base_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(base_dir, "frontend")
frontend_env_path = os.path.join(frontend_dir, ".env")


def log_vite_output(pipe):
    while True:
        line_bytes = pipe.readline()
        if not line_bytes:
            break
        line = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
        if line:
            if any(
                word in line.lower()
                for word in ["error", "failed", "exception", "vite error"]
            ):
                logger.log("ERROR", f"{line}")
            else:
                logger.log("INFO", f"{line}")


def run_vite_with_logging(frontend_dir: str):
    cmd = "npm run dev"

    process = None
    interrupted = False  # Flag pour distinguer interruption user vs. crash réel

    try:
        process = subprocess.Popen(
            cmd,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Fusionne stderr dans stdout
            bufsize=0,  # Lecture non tamponnée
            universal_newlines=False,  # Mode binaire pour décoder manuellement
            shell=True,  # Nécessaire pour Windows avec npm
        )
    except FileNotFoundError:
        logger.error(
            "❌ npm n'est pas trouvé. Vérifiez que Node.js est installé et dans le PATH."
        )
        return
    except Exception as e:
        logger.error(f"❌ Erreur lors du lancement de npm : {e}")
        return

    # Thread pour logger stdout en live (démarre avant wait pour ne rien rater)
    stdout_thread = threading.Thread(target=log_vite_output, args=(process.stdout,))
    stdout_thread.daemon = True
    stdout_thread.start()

    try:
        # Attendre la fin du processus (bloquant)
        process.wait()
    except KeyboardInterrupt:
        interrupted = True
        logger.info("🛑 Interruption détectée (Ctrl+C). Arrêt de Vite...")
        if process:
            process.terminate()  # Signal doux (WM_CLOSE sur Windows)
            try:
                # Attendre un peu pour un arrêt gracieux (timeout 5s)
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Vite ne s'arrête pas gracieusement. Kill forcé.")
                process.kill()  # Signal dur si besoin
                process.wait()  # Récupère le code de retour

    # Attendre que le thread de log se termine (optionnel, mais propre)
    stdout_thread.join(timeout=1)

    # Vérifier le code de retour **seulement si pas d'interruption user**
    if process:
        returncode = process.returncode
        if interrupted:
            logger.info("✅ Vite s'est arrêté proprement.")
        elif returncode != 0:
            logger.error(
                f"❌ Vite s'est terminé avec code d'erreur {returncode} (crash inattendu)."
            )


if __name__ == "__main__":
    __name__ = "Script run_frontend"

    with open(frontend_env_path, "w") as f:
        f.write(f"VITE_PORT={PORT_FRONT}\n")
        f.write(f"VITE_PORT_BACK={PORT_BACK}\n")
        f.write(f"VITE_APP_NAME={APP_NAME}\n")
        f.write(f"VITE_ENV={ENV}\n")
        f.write(f"VITE_PRINTFUL={PRINTFUL}\n")
        f.write(f"VITE_PAYPAL_CLIENT_ID={PAYPAL_CLIENT_ID}\n")

    logger.info(f"✅ File '{frontend_env_path}' successfully generated.")

    __name__ = "Vite"
    run_vite_with_logging(frontend_dir)
