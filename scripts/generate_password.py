# flake8: noqa: E402
import secrets
import string
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.utils.logger_config import configure_logger

logger = configure_logger()

def generate_password(length=18):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%^&*()-_=+" for c in password)):
            return password

password = generate_password()

logger.info(f"Generated secure password : {password}")
