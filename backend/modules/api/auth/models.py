from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from modules.database.session import UsersBase
from datetime import datetime, timezone


class RefreshToken(UsersBase):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    revoked = Column(Boolean, default=False, nullable=False)

    users = relationship("User", back_populates="refresh_tokens")
