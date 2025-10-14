from sqlalchemy import (
    Column,
    Integer,
    String,
)
from modules.database.session import UsersBase


class Event(UsersBase):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    organiser = Column(String, nullable=True)
    place = Column(String, nullable=True)
    date = Column(String, nullable=False)
