from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from utils.logger_config import configure_logger
from modules.database.dependencies import get_users_db
from modules.api.users.functions import (
    get_current_user,
    get_user_by_email,
    get_current_user_optional,
)
from modules.api.users.schemas import UserResponse, UserCreate, UserUpdate, TokenData
from modules.api.users.models import User, Role
from modules.api.auth.security import hash_password
from typing import Optional
from modules.api.users.telegram import notify_telegram


logger = configure_logger()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

users_router = APIRouter()


@users_router.get("/users/me", response_model=UserResponse)
def read_users_me(
    security_scopes: SecurityScopes,
    token_data: TokenData = Depends(get_current_user),
    db: Session = Depends(get_users_db),
):
    user = get_user_by_email(token_data.sub, db)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        name=user.name,
        nickname=user.nickname,
        discord=user.discord,
        email=user.email,
        is_active=user.is_active,
        role=user.role.role,
        scopes=token_data.scopes,
    )


@users_router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Retrieve a user by ID",
    description="Returns the information of a specific user based on their ID.",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden")

    user = (
        db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        name=user.name,
        nickname=user.nickname,
        discord=user.discord,
        email=user.email,
        is_active=user.is_active,
        role=user.role.role,
    )


@users_router.get("/users", response_model=list[UserResponse])
def get_all_users(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_users_db)
):
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=403, detail="Access denied: administrators only."
        )

    users = db.query(User).all()

    response = []
    for user in users:
        response.append(
            UserResponse(
                id=user.id,
                name=user.name,
                nickname=user.nickname,
                discord=user.discord,
                email=user.email,
                is_active=user.is_active,
                role=user.role.role,
            )
        )

    return response


@users_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_users_db),
):
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=403,
            detail="Access denied: administrators only.",
        )

    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found.")

    db.delete(user_to_delete)
    db.commit()

    return JSONResponse({"message": "User deleted"})


@users_router.post(
    "/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_users_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    # Check if the user is an admin
    is_admin = (
        current_user
        and current_user.get("scopes")
        and "admin" in current_user.get("scopes")
    )

    # Validate email if provided and not admin
    if user_data.email and not is_admin:
        existing_user_email = db.query(User).filter_by(email=user_data.email).first()
        if existing_user_email:
            raise HTTPException(
                status_code=400, detail="A user with this email already exists."
            )

    # Check if a user with the same name already exists
    existing_user_name = db.query(User).filter_by(name=user_data.name).first()
    if existing_user_name:
        raise HTTPException(
            status_code=400, detail="A user with this name already exists."
        )

    # Check if a user with the nickname name already exists
    existing_user_nickname = (
        db.query(User).filter_by(nickname=user_data.nickname).first()
    )
    if existing_user_nickname:
        raise HTTPException(
            status_code=400, detail="A user with this nickname already exists."
        )

    # Validate password if provided and not admin
    if not is_admin and not user_data.password:
        raise HTTPException(
            status_code=400, detail="Password is required for non-admin user creation."
        )

    role_name = user_data.role if user_data.role else "player"

    if is_admin and user_data.role:
        role_name = user_data.role
    else:
        role_name = "player"

    role_obj = db.query(Role).filter_by(role=role_name).first()
    if not role_obj:
        raise HTTPException(
            status_code=400 if role_name != "player" else 500,
            detail=f"The role '{role_name}' could not be found.",
        )

    new_user = User(
        email=user_data.email,
        name=user_data.name,
        nickname=user_data.nickname,
        discord=user_data.discord,
        hashed_password=hash_password(user_data.password)
        if user_data.password
        else None,
        role_id=role_obj.id,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    class NotifyUserCreate:
        def __init__(self, name, email, role, type):
            self.name = name
            self.email = email
            self.role = role
            self.type = type

    notify_user = NotifyUserCreate(
        name=new_user.name,
        email=new_user.email,
        role=new_user.role.role,
        type="userCreate",
    )

    notify_telegram(notify_user)

    logger.info(f"User {new_user.name} successfully created")

    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        nickname=new_user.nickname,
        discord=new_user.discord,
        email=new_user.email,
        is_active=new_user.is_active,
        role=new_user.role.role,
    )


@users_router.patch("/users/me", response_model=UserResponse)
def update_current_user(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_users_db),
):
    user = get_user_by_email(current_user.sub, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Check for duplicate name (excluding the current user)
    if update_data.name and update_data.name != user.name:
        existing_user_name = (
            db.query(User)
            .filter_by(name=update_data.name)
            .filter(User.id != user.id)
            .first()
        )
        if existing_user_name:
            raise HTTPException(
                status_code=400, detail="A user with this name already exists."
            )

    # Check for duplicate nickname (excluding the current user)
    if update_data.nickname and update_data.nickname != user.nickname:
        existing_user_nickname = (
            db.query(User)
            .filter_by(nickname=update_data.nickname)
            .filter(User.id != user.id)
            .first()
        )
        if existing_user_nickname:
            raise HTTPException(
                status_code=400, detail="A user with this nickname already exists."
            )

    # Check for duplicate email (if applicable)
    if update_data.email and update_data.email != user.email:
        existing_user_email = get_user_by_email(update_data.email, db)
        if existing_user_email:
            raise HTTPException(
                status_code=400, detail="A user with this email already exists."
            )

    # Update fields
    if update_data.name:
        user.name = update_data.name

    if update_data.nickname:
        user.nickname = update_data.nickname

    if update_data.discord:
        user.discord = update_data.discord

    if update_data.email:
        user.email = update_data.email

    if update_data.password:
        user.hashed_password = hash_password(update_data.password)

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        name=user.name,
        nickname=user.nickname,
        discord=user.discord,
        email=user.email,
        is_active=user.is_active,
        role=user.role.role,
    )


@users_router.patch("/users/{user_id}", response_model=UserResponse)
def admin_update_user(
    user_id: int,
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_users_db),
):
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=403, detail="Access denied: administrators only."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if update_data.name:
        user.name = update_data.name

    if update_data.nickname:
        user.nickname = update_data.nickname

    if update_data.discord:
        user.discord = update_data.discord

    if update_data.email:
        user.email = update_data.email

    if update_data.password:
        user.hashed_password = hash_password(update_data.password)

    if update_data.role:
        role_obj = db.query(Role).filter(Role.role == update_data.role).first()
        if not role_obj:
            raise HTTPException(status_code=400, detail="Invalid role provided.")
        user.role = role_obj

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        name=user.name,
        nickname=user.nickname,
        discord=user.discord,
        email=user.email,
        is_active=user.is_active,
        role=user.role.role,
    )
