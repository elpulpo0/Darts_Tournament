from sqlalchemy import Column, Integer, String
from modules.database.session import UsersBase


class Inscription(UsersBase):
    __tablename__ = "inscriptions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    club = Column(String, nullable=False)
    player_number = Column(Integer, nullable=True)
    category_simple = Column(String, nullable=True)
    category_double = Column(String, nullable=True)
    doublette = Column(Integer, nullable=True)
