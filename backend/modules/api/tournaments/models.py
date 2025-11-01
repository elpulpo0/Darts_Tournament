from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Float,
    Table,
    Index,
)
from sqlalchemy.orm import relationship
from modules.database.session import UsersBase
from datetime import datetime

# Table d’association pour Participant <-> Pool (ManyToMany)
pool_participant_association = Table(
    "pool_participant_association",
    UsersBase.metadata,
    Column("pool_id", Integer, ForeignKey("pools.id"), primary_key=True),
    Column("participant_id", Integer, ForeignKey("participants.id"), primary_key=True),
)


class Participant(UsersBase):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    name = Column(
        String, nullable=True
    )  # Nom du participant (vide pour singles, custom pour doubles)

    tournament = relationship("Tournament", back_populates="participants")
    members = relationship(
        "ParticipantMember", back_populates="participant", cascade="all, delete-orphan"
    )  # Renommé de team_members
    pools = relationship(
        "Pool", secondary=pool_participant_association, back_populates="participants"
    )
    matches = relationship(
        "Match",
        secondary="match_players",
        back_populates="participants",
        overlaps="match_participations",
    )
    match_participations = relationship(
        "MatchPlayer",
        back_populates="participant",
        overlaps="matches",
    )


class ParticipantMember(UsersBase):
    __tablename__ = "participant_members"

    participant_id = Column(Integer, ForeignKey("participants.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    participant = relationship("Participant", back_populates="members")
    user = relationship("User", back_populates="participant_memberships")


class Tournament(UsersBase):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    type = Column(String, nullable=True, index=True)  # 'pool' or 'elimination'
    mode = Column(String, nullable=True, index=True)  # 'single' or 'double'
    status = Column(
        String, default="open", index=True
    )  # 'open', 'running', 'finished', 'closed'

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
    participants = relationship(
        "Participant", back_populates="tournament", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_tournament_mode_status", "mode", "status"),)


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
    participants = relationship(
        "Participant", secondary=pool_participant_association, back_populates="pools"
    )
    matches = relationship("Match", back_populates="pool")


class Match(UsersBase):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=True)
    status = Column(
        String, default="pending", index=True
    )  # pending, completed, cancelled
    round = Column(Integer, default=1)

    tournament = relationship("Tournament", back_populates="matches")
    pool = relationship("Pool", back_populates="matches")
    participants = relationship(
        "Participant",
        secondary="match_players",
        back_populates="matches",
        overlaps="match_participations",
    )
    match_participations = relationship(
        "MatchPlayer",
        back_populates="match",
        cascade="all, delete-orphan",
        overlaps="participants",
    )

    __table_args__ = (Index("ix_match_status", "status"),)


class MatchPlayer(UsersBase):
    __tablename__ = "match_players"

    match_id = Column(Integer, ForeignKey("matches.id"), primary_key=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), primary_key=True)
    score = Column(Float, nullable=True)  # Score ou points attribués dans le match

    match = relationship(
        "Match",
        back_populates="match_participations",
        overlaps="matches,participants",
    )
    participant = relationship(
        "Participant",
        back_populates="match_participations",
        overlaps="matches,participants",
    )


class TournamentPayment(UsersBase):
    __tablename__ = "tournament_payments"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), primary_key=True)
    paid = Column(Boolean, default=False)
