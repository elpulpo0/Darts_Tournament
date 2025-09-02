from sqlalchemy.orm import Session
from dotenv import load_dotenv

# from modules.api.auth.security import hash_password
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

    sync_users_from_yaml()


def load_initial_users_config():
    """
    Load the initial user and role configuration from the YAML config file.
    """
    if not INITIAL_USERS_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {INITIAL_USERS_CONFIG_PATH}")
    with open(INITIAL_USERS_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def sync_users_from_yaml():
    """
    Sync users from the YAML config file with the database.
    Creates roles and adds users from YAML if they don't exist in the database (based on email).
    """
    config = load_initial_users_config()
    db: Session = UsersSessionLocal()

    try:
        # Ensure all roles from YAML exist in the database
        for role_name in config.get("roles", []):
            if not db.query(Role).filter_by(role=role_name).first():
                db.add(Role(role=role_name))
        db.commit()

        # Get all role mappings
        roles = {role.role: role.id for role in db.query(Role).all()}

        # Check each user in the YAML config
        for user_cfg in config.get("users", []):
            role_id = roles.get(user_cfg["role"])
            if not role_id:
                raise ValueError(f"The role '{user_cfg['role']}' does not exist.")

            # Check if user exists in the database by email
            if not db.query(User).filter_by(email=user_cfg["email"]).first():
                user = User(
                    email=user_cfg["email"],
                    name=user_cfg["name"],
                    # hashed_password=hash_password(user_cfg["password"]),
                    hashed_password=user_cfg["password"],
                    role_id=role_id,
                    is_active=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(
                    f"User '{user.name}' was successfully added from YAML config."
                )
            else:
                logger.debug(
                    f"User with email '{user_cfg['email']}' already exists in the database."
                )

    except Exception as e:
        db.rollback()
        logger.error(f"Error while syncing users from YAML: {e}")
        raise
    finally:
        db.close()
