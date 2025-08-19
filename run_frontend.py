import os
from dotenv import load_dotenv
import subprocess
from backend.utils.logger_config import configure_logger

logger = configure_logger()

load_dotenv()

PORT_BACK = os.getenv("PORT_BACK")
APP_NAME = os.getenv("APP_NAME")
PORT_FRONT = os.getenv("PORT_FRONT")
ENV = os.getenv("ENV")

base_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(base_dir, "frontend")
frontend_env_path = os.path.join(frontend_dir, ".env")

with open(frontend_env_path, "w") as f:
    f.write(f"VITE_PORT={PORT_FRONT}\n")
    f.write(f"VITE_PORT_BACK={PORT_BACK}\n")
    f.write(f"VITE_APP_NAME={APP_NAME}\n")
    f.write(f"VITE_ENV={ENV}\n")

logger.info(f"✅ File '{frontend_env_path}' successfully generated.")

try:
    subprocess.run("npm run dev", cwd=frontend_dir, shell=True, check=True)
except subprocess.CalledProcessError as e:
    logger.error(f"❌ Error running npm: {e}")
