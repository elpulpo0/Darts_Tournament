from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List


class TournamentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: datetime
    is_active: bool = True
    type: Optional[str] = None  # 'pool' ou 'elimination', nullable
    mode: Optional[str] = None  # 'single' or 'double'
    status: str = "open"  # Statut unique ('open', 'running', 'finished', 'closed'), default 'open'


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    type: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[str] = None


class TournamentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    start_date: datetime
    is_active: bool
    type: Optional[str]
    mode: Optional[str]
    status: str
    model_config = ConfigDict(from_attributes=True)


class TournamentRegistrationCreate(BaseModel):
    tournament_id: int
    user_id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None


class TournamentRegistrationResponse(BaseModel):
    id: int
    user_id: int
    tournament_id: int
    registration_date: datetime
    model_config = ConfigDict(from_attributes=True)


class ParticipantCreate(BaseModel):
    name: Optional[str] = None  # Optionnel pour single (généré), requis pour double
    user_ids: List[int]  # 1 pour single, 2 pour double


class ParticipantResponse(BaseModel):
    id: int
    name: str
    users: List["PlayerResponse"]  # Toujours une liste (1 ou 2)
    model_config = ConfigDict(from_attributes=True)


class MatchCreate(BaseModel):
    tournament_id: int
    participant_ids: List[int]  # Liste des IDs des participants (players or teams)
    status: Optional[str] = "pending"
    pool_id: Optional[int] = None
    round: Optional[int] = 1

    @field_validator("participant_ids")
    @classmethod
    def validate_participant_ids(cls, v):
        if len(v) != 2:
            raise ValueError("Match must have exactly 2 participants")
        return v


class MatchUpdate(BaseModel):
    status: Optional[str] = None
    scores: Optional[List[dict]] = None  # Liste de {participant_id: int, score: float}


class PlayerResponse(BaseModel):
    id: int
    name: Optional[str]
    nickname: str
    model_config = ConfigDict(from_attributes=True)


class MatchResponse(BaseModel):
    id: int
    tournament_id: int
    status: str
    participants: List[dict]  # Liste de {participant_id: int, name: str, score: float}
    pool_id: Optional[int] = None
    round: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class PoolResponse(BaseModel):
    id: int
    name: Optional[str] = None
    participants: List[ParticipantResponse]
    matches: List[MatchResponse]
    model_config = ConfigDict(from_attributes=True)


class PoolCreate(BaseModel):
    name: Optional[str] = None
    participant_ids: List[int]


class LeaderboardEntry(BaseModel):
    user_id: int
    name: Optional[str] = "Inconnu"
    nickname: str
    total_points: float
    single_wins: float
    double_wins: float
    single_manches: float
    double_manches: float

    class Config:
        orm_mode = True


class TournamentLeaderboardEntry(BaseModel):
    participant_id: int
    nickname: str
    wins: int
    total_manches: float


class TournamentLeaderboardResponse(BaseModel):
    tournament_id: int
    leaderboard: List[TournamentLeaderboardEntry]


class SeasonLeaderboardResponse(BaseModel):
    season: str
    leaderboard: List[LeaderboardEntry]


class PoolLeaderboardResponse(BaseModel):
    tournament_id: int
    pool_id: int
    pool_name: str
    leaderboard: List[TournamentLeaderboardEntry]
    model_config = ConfigDict(from_attributes=True)


class ParticipantBasicSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MatchParticipantSchema(BaseModel):
    id: int
    name: str
    score: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class MatchDetailSchema(BaseModel):
    id: int
    participants: List[MatchParticipantSchema]
    status: str
    pool_id: Optional[int] = None
    round: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class PoolDetailSchema(BaseModel):
    id: int
    name: Optional[str] = None
    participants: List[ParticipantBasicSchema]
    matches: List[MatchDetailSchema]
    model_config = ConfigDict(from_attributes=True)


class TournamentFullDetailSchema(BaseModel):
    id: int
    name: str
    type: Optional[str]
    mode: Optional[str]
    status: str
    pools: List[PoolDetailSchema]
    final_matches: List[MatchDetailSchema]
    model_config = ConfigDict(from_attributes=True)
