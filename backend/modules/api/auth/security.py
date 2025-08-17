import hashlib
import bcrypt


def anonymize(name: str) -> str:
    """Return the SHA‑256 hash of a given first or last name,
    used to anonymize personal data."""
    return hashlib.sha256(name.encode("utf-8")).hexdigest()


def hash_token(token: str) -> str:
    """Return the SHA‑256 hash of a refresh token so it can be stored safely."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """Generate a unique salt and return the bcrypt hash of a plaintext password."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check whether a plaintext password matches the stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
