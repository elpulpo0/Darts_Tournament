from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Float,
    Table,
)
from sqlalchemy.orm import relationship
from modules.database.session import UsersBase
from datetime import datetime

# Table d’association pour User <-> Pool (ManyToMany)
pool_player_association = Table(
    "pool_player_association",
    UsersBase.metadata,
    Column("pool_id", Integer, ForeignKey("pools.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)


class Tournament(UsersBase):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    type = Column(String, nullable=True)  # 'pool' ou 'elimination'
    status = Column(String, default="open")  # 'open', 'running', 'closed'

    registrations = relationship(
        "TournamentRegistration",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
    matches = relationship(
        "Match", back_populates="tournament", cascade="all, delete-orphan"
    )
    pools = relationship(
        "Pool", back_populates="tournament", cascade="all, delete-orphan"
    )


class TournamentRegistration(UsersBase):
    __tablename__ = "tournament_registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tournaments")
    tournament = relationship("Tournament", back_populates="registrations")


class Pool(UsersBase):
    __tablename__ = "pools"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    name = Column(String, nullable=True)

    tournament = relationship("Tournament", back_populates="pools")
    players = relationship(
        "User", secondary=pool_player_association, back_populates="pools"
    )
    matches = relationship("Match", back_populates="pool")


class Match(UsersBase):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=True)

    status = Column(String, default="pending")  # pending, completed, cancelled

    round = Column(Integer, default=1)

    tournament = relationship("Tournament", back_populates="matches")
    pool = relationship("Pool", back_populates="matches")
    players = relationship(
        "User",
        secondary="match_players",
        back_populates="matches",
        overlaps="match_players",
    )
    match_players = relationship(
        "MatchPlayer",
        back_populates="match",
        cascade="all, delete-orphan",
        overlaps="players",
    )


class MatchPlayer(UsersBase):
    __tablename__ = "match_players"

    match_id = Column(Integer, ForeignKey("matches.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    score = Column(Float, nullable=True)  # Score ou points attribués dans le match

    match = relationship(
        "Match",
        back_populates="match_players",
        overlaps="matches,players",
    )
    user = relationship(
        "User",
        back_populates="match_players",
        overlaps="matches,players",
    )
