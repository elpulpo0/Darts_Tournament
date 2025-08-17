from sqlalchemy.orm import Session
from dotenv import load_dotenv

from modules.api.auth.security import hash_password
from utils.logger_config import configure_logger
from modules.api.users.models import User, Role
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
        create_roles_and_first_users()
    else:
        logger.info("The 'users' database already exists. No changes needed.")


def load_initial_users_config():
    """
    Load the initial user and role configuration from the YAML config file.
    """
    if not INITIAL_USERS_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {INITIAL_USERS_CONFIG_PATH}")
    with open(INITIAL_USERS_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def create_roles_and_first_users():
    """
    Create roles and first users as defined in the initial configuration file.
    Raises an exception if something goes wrong during creation.
    """
    config = load_initial_users_config()
    db: Session = UsersSessionLocal()

    try:
        for role_name in config.get("roles", []):
            if not db.query(Role).filter_by(role=role_name).first():
                db.add(Role(role=role_name))
        db.commit()

        roles = {role.role: role.id for role in db.query(Role).all()}

        for user_cfg in config.get("users", []):
            role_id = roles.get(user_cfg["role"])
            if not role_id:
                raise ValueError(f"The role '{user_cfg['role']}' does not exist.")

            if db.query(User).filter_by(email=user_cfg["email"]).first():
                continue

            user = User(
                email=user_cfg["email"],
                name=user_cfg["name"],
                hashed_password=hash_password(user_cfg["password"]),
                role_id=role_id,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"User '{user.name}' was successfully created.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error while creating initial users: {e}")
        raise
    finally:
        db.close()
