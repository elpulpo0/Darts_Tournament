from modules.api.users.create_db import User
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import SecurityScopes, OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from utils.logger_config import configure_logger
from dotenv import load_dotenv
import os
from modules.api.users.schemas import TokenData
from modules.database.dependencies import get_users_db
from pydantic import ValidationError
from jose import JWTError, jwt
from typing import Optional

logger = configure_logger()

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    scopes={
        "me": "Access to personal information",
        "admin": "Access to administrative operations",
        "editor": "Access to edit resources",
        "reader": "Read-only access to resources",
    },
)


def get_user_by_email(email: str, db: Session):
    """
    Retrieve a user from the database by anonymized email.
    """
    user = db.query(User).filter(User.email == email).first()
    return user


def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_users_db),
):
    """
    Validate JWT token, check scopes, and retrieve the current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenData(**payload)
        email = token_data.sub
        token_scopes = token_data.scopes

    except JWTError:
        raise credentials_exception
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token payload validation error: {e.errors()}",
        )

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

    user = get_user_by_email(email, db)
    if not user:
        raise credentials_exception

    return TokenData(
        sub=user.email,
        exp=token_data.exp,
        role=user.role.role,
        scopes=token_data.scopes,
        id=user.id,
    )


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_users_db),
) -> Optional[dict]:
    """
    Try to decode the JWT and get user info. Return None if not authenticated.
    """
    auth = request.headers.get("Authorization")
    if not auth:
        return None

    scheme, token = get_authorization_scheme_param(auth)
    if scheme.lower() != "bearer" or not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenData(**payload)
        user = get_user_by_email(token_data.sub, db)

        if not user:
            return None

        return payload  # or return token_data

    except (JWTError, ValidationError):
        return None
