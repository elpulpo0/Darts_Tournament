from modules.api.auth.security import verify_password, anonymize, hash_token
from datetime import datetime, timedelta, UTC
from zoneinfo import ZoneInfo
from jose import jwt
import os
from dotenv import load_dotenv
from utils.logger_config import configure_logger
from modules.api.users.functions import get_user_by_email
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from modules.api.auth.models import RefreshToken
from modules.api.users.telegram import notify_telegram


logger = configure_logger()

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


class NotifyUserLogin:
    def __init__(self, name, role, scopes, type):
        self.name = name
        self.role = role
        self.scopes = scopes
        self.type = type


def create_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta else timedelta(minutes=60)
    )
    role = data.get("role")
    name = data.get("name")

    scopes_map = {
        "admin": ["admin", "editor", "player", "me"],
        "editor": ["editor", "player", "me"],
        "player": ["player", "me"],
        "user": ["me"],
    }

    scopes = scopes_map.get(role, [])

    token_type = data.get("type", "access")
    to_encode["token_type"] = token_type

    if token_type == "access":
        to_encode["scopes"] = scopes

    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    local_tz = ZoneInfo("Europe/Paris")
    expire_local = expire.astimezone(local_tz)

    if token_type == "access":
        logger.info(
            f"Token {token_type} created (role: {role}) with scopes {scopes} - "
            f"Expire at {expire_local.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if not os.getenv("TEST_MODE") and os.getenv("ENV") != "dev":
            notify_user = NotifyUserLogin(
                name=name, role=role, scopes=scopes, type="login"
            )
            notify_telegram(notify_user)

    else:
        logger.info(
            f"Token {token_type} created - "
            f"Expire at {expire_local.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str):
    """Authenticate a user by verifying their email and password."""

    user = get_user_by_email(email, db)

    if not user:
        logger.info("User not found.")
        return False

    if not verify_password(password, user.hashed_password):
        logger.info("Invalid password.")
        return False

    logger.info(f"{user.name.upper()} successfully authenticated")
    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.role,
        "name": user.name,
    }


def store_refresh_token(db: Session, user_id: int, token: str, expires_at: datetime):
    # Revoke existing tokens
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked.is_(False),
    ).update({RefreshToken.revoked: True}, synchronize_session=False)

    # Try to insert a new token, handle duplicates safely
    new_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
        revoked=False,
    )

    db.add(new_token)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.error("Duplicate refresh token encountered — regenerating.")
        raise ValueError("Token collision occurred, please try again.")


def find_refresh_token(db: Session, hashed_token: str) -> RefreshToken | None:
    refresh_token = (
        db.query(RefreshToken).filter(RefreshToken.token == hashed_token).first()
    )
    if refresh_token:
        logger.info(
            f"""
            Refresh token found: {refresh_token.token},
            expires_at: {refresh_token.expires_at}
            """
        )
    else:
        logger.warning("No refresh token found.")
    return refresh_token


def verify_token(provided_token: str, stored_hash: str) -> bool:
    return hash_token(provided_token) == stored_hash
