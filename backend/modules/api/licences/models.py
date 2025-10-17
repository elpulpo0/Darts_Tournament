from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from modules.database.session import UsersBase


class Licence(UsersBase):
    __tablename__ = "licences"

    id = Column(Integer, primary_key=True, index=True)
    ligue = Column(String, nullable=False)
    comite = Column(String, nullable=False)
    club_number = Column(Integer, nullable=False)
    club_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    category = Column(String, nullable=False)
    licence_number = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates=None)
