from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pydantic import ValidationError

# from modules.api.auth.security import hash_password
from utils.logger_config import configure_logger
from modules.api.users.models import User, Role
from modules.api.users.schemas import UserCreate
from modules.database.config import USERS_DATABASE_PATH, INITIAL_USERS_CONFIG_PATH
from modules.database.session import users_engine, UsersSessionLocal, UsersBase
import yaml

logger = configure_logger()

load_dotenv()


def init_users_db():
    """
    Check if the users database exists and create it with initial admin if not.
    """
    db_exists = USERS_DATABASE_PATH.exists()

    if not db_exists:
        logger.info("The 'users' database does not exist. Creating it...")
        UsersBase.metadata.create_all(bind=users_engine)
        logger.info("The 'users' database was successfully created.")

    UsersBase.metadata.create_all(bind=users_engine)

    # sync_users_from_yaml()


def load_initial_users_config():
    """
    Load the initial user and role configuration from the YAML config file.
    """
    if not INITIAL_USERS_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {INITIAL_USERS_CONFIG_PATH}")
    with open(INITIAL_USERS_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def sync_users_from_yaml():
    """
    Sync users from the YAML config file with the database.
    Creates roles and adds users from YAML if they don't exist in the database (based on email or name).
    """
    config = load_initial_users_config()
    db: Session = UsersSessionLocal()

    try:
        # Ensure all roles from YAML exist in the database
        for role_name in config.get("roles", []):
            if not db.query(Role).filter_by(role=role_name).first():
                db.add(Role(role=role_name))
        db.commit()

        roles = {role.role: role.id for role in db.query(Role).all()}

        # Process each user in the YAML config
        for user_cfg in config.get("users", []):
            try:
                # Validate user data with Pydantic
                user_data = UserCreate(**user_cfg)
            except ValidationError as e:
                logger.warning(
                    f"Invalid user data for {user_cfg.get('name', user_cfg.get('nickname', 'Unknown'))}: {e}"
                )
                continue

            # Check for duplicate email (if provided)
            if (
                user_data.email
                and db.query(User).filter_by(email=user_data.email).first()
            ):
                logger.debug(
                    f"User with email '{user_data.email}' already exists in the database."
                )
                continue

            # Check for duplicate name (if provided)
            if user_data.name and db.query(User).filter_by(name=user_data.name).first():
                logger.debug(
                    f"User with name '{user_data.name}' already exists in the database."
                )
                continue

            # Check for duplicate nickname (if provided)
            if (
                user_data.nickname
                and db.query(User).filter_by(nickname=user_data.nickname).first()
            ):
                logger.debug(
                    f"User with nickname '{user_data.nickname}' already exists in the database."
                )
                continue

            # Validate role
            role_id = roles.get(user_data.role or "player")
            if not role_id:
                logger.error(
                    f"Role '{user_data.role or 'player'}' does not exist for user {user_data.name or user_data.nickname or 'Unknown'}"
                )
                continue

            # Create user
            user = User(
                email=user_data.email,
                name=user_data.name,
                nickname=user_data.nickname,
                discord=user_data.discord,
                hashed_password=user_data.password
                # hashed_password=hash_password(user_data.password)
                if user_data.password
                else None,
                role_id=role_id,
                is_active=True,
            )
            db.add(user)
            logger.info(
                f"User '{user.name or user.nickname or user.email or 'Unknown'}' created."
            )

        db.commit()  # Commit all changes at once
        logger.info("All users and roles successfully synced.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error while syncing users from YAML: {e}")
        raise
    finally:
        db.close()
