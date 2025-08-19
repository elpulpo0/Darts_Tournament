from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class TournamentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: datetime
    is_active: bool = True
    type: Optional[str] = None  # 'pool' ou 'elimination', nullable
    status: str = "open"  # Statut unique ('open', 'running', 'closed'), default 'open'


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    type: Optional[str] = None
    status: Optional[str] = None


class TournamentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    start_date: datetime
    is_active: bool
    type: Optional[str]
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


class MatchCreate(BaseModel):
    tournament_id: int
    player_ids: List[int]  # Liste des IDs des joueurs participant au match
    status: Optional[str] = "pending"
    pool_id: Optional[int] = None
    round: Optional[int] = 1


class MatchUpdate(BaseModel):
    status: Optional[str] = None
    scores: Optional[List[dict]] = None  # Liste de {user_id: int, score: float}


class PlayerResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MatchResponse(BaseModel):
    id: int
    tournament_id: int
    status: str
    players: List[dict]  # Liste de {user_id: int, name: str, score: float}
    pool_id: Optional[int] = None
    round: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class PoolResponse(BaseModel):
    id: int
    name: Optional[str] = None
    players: List[PlayerResponse]
    matches: List[MatchResponse]
    model_config = ConfigDict(from_attributes=True)


class PoolCreate(BaseModel):
    name: Optional[str] = None
    player_ids: List[int]


class LeaderboardEntry(BaseModel):
    user_id: int
    name: str
    total_points: float
    wins: int
    total_manches: int


class TournamentLeaderboardEntry(BaseModel):
    user_id: int
    name: str
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


# Pour les projections détaillées
class PlayerBasicSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MatchPlayerSchema(BaseModel):
    id: int
    name: str
    score: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class MatchDetailSchema(BaseModel):
    id: int
    players: List[MatchPlayerSchema]
    status: str
    pool_id: Optional[int] = None
    round: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class PoolDetailSchema(BaseModel):
    id: int
    name: Optional[str] = None
    players: List[PlayerBasicSchema]
    matches: List[MatchDetailSchema]
    model_config = ConfigDict(from_attributes=True)


class TournamentFullDetailSchema(BaseModel):
    id: int
    name: str
    type: Optional[str]
    status: str
    pools: List[PoolDetailSchema]
    final_matches: List[MatchDetailSchema]
    model_config = ConfigDict(from_attributes=True)
