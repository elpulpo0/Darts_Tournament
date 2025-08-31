from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from modules.api.auth.models import RefreshToken  # noqa: F401
from sqlalchemy.orm import relationship
from modules.database.session import UsersBase


class User(UsersBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    role = relationship("Role", back_populates="users")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="users", cascade="all, delete-orphan"
    )
    tournaments = relationship("TournamentRegistration", back_populates="user")
    participant_memberships = relationship("ParticipantMember", back_populates="user")


class Role(UsersBase):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, unique=True, index=True)

    users = relationship("User", back_populates="role")
