from utils.logger_config import configure_logger
from datetime import timedelta, timezone, datetime
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status
from modules.api.auth.schemas import Token
from modules.api.users.models import User
from modules.api.auth.models import RefreshToken
from modules.database.dependencies import get_users_db
from sqlalchemy.orm import Session
from modules.api.auth.functions import (
    authenticate_user,
    create_token,
    store_refresh_token,
)
import os
from fastapi import Request
from jose import JWTError, jwt
from modules.api.users.functions import (
    get_user_by_email,
    oauth2_scheme,
    get_current_user,
)
from modules.api.auth.functions import find_refresh_token
from modules.api.auth.security import hash_token

from fastapi.responses import JSONResponse
from uuid import uuid4
from typing import List

load_dotenv()

logger = configure_logger()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

auth_router = APIRouter()


@auth_router.post("/login", response_model=Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_users_db),
):
    user_data = authenticate_user(db, form_data.username, form_data.password)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=15)
    refresh_token_expires = timedelta(days=7)

    access_token = create_token(
        data={
            "sub": user_data["email"],
            "role": user_data["role"],
            "type": "access",
            "name": user_data["name"],
        },
        expires_delta=access_token_expires,
    )

    refresh_token = create_token(
        data={"sub": user_data["email"], "type": "refresh"},
        expires_delta=refresh_token_expires,
    )

    refresh_expiry = datetime.now(timezone.utc) + refresh_token_expires
    hashed_token = hash_token(refresh_token)
    store_refresh_token(db, user_data["user_id"], hashed_token, refresh_expiry)

    return JSONResponse(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    )


@auth_router.post("/refresh", response_model=Token)
def refresh_token(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_users_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token for refresh")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    hashed_token = hash_token(token)
    refresh_token_db = find_refresh_token(db, hashed_token)

    if not refresh_token_db:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    if refresh_token_db.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    ):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    refresh_token_db.revoked = True

    user = get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_access_token = create_token(
        data={"sub": email, "role": role}, expires_delta=timedelta(minutes=15)
    )

    new_refresh_token = create_token(
        data={"sub": email, "role": role, "type": "refresh", "jti": str(uuid4())},
        expires_delta=timedelta(days=7),
    )
    hashed_new_refresh_token = hash_token(new_refresh_token)
    refresh_expiry = datetime.now(timezone.utc) + timedelta(days=7)

    store_refresh_token(
        db, user_id=user.id, token=hashed_new_refresh_token, expires_at=refresh_expiry
    )

    db.commit()

    return JSONResponse(
        {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    )


@auth_router.get("/refresh-tokens", response_model=List[dict])
def list_refresh_tokens(
    db: Session = Depends(get_users_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")

    tokens = db.query(RefreshToken).all()
    return [
        {
            "user_id": token.user_id,
            "token": token.token[:10] + "...",
            "created_at": token.created_at,
            "expires_at": token.expires_at,
            "revoked": token.revoked,
        }
        for token in tokens
    ]
