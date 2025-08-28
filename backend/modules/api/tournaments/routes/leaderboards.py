from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, case, desc, or_, and_, literal, union_all
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import literal_column
from modules.database.dependencies import get_users_db
from modules.api.tournaments.models import Tournament, Match, MatchPlayer, Pool, Participant, TeamMember
from modules.api.tournaments.schemas import (
    TournamentLeaderboardResponse,
    TournamentLeaderboardEntry,
    SeasonLeaderboardResponse,
    LeaderboardEntry,
    PoolLeaderboardResponse,
)
from modules.api.users.models import User
from typing import List

leaderboards_router = APIRouter(prefix="/tournaments", tags=["leaderboards"])


@leaderboards_router.get("/{tournament_id}/leaderboard", response_model=TournamentLeaderboardResponse)
def get_tournament_leaderboard(
    tournament_id: int,
    db: Session = Depends(get_users_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Subquery pour trouver le score de l'adversaire dans chaque match
    other_score_subquery = (
        select(
            MatchPlayer.match_id,
            MatchPlayer.participant_id.label("other_participant_id"),
            MatchPlayer.score.label("other_score"),
        )
        .subquery()
    )

    # Query pour compter les victoires et sommer les manches par participant
    leaderboard_query = (
        select(
            MatchPlayer.participant_id,
            func.sum(MatchPlayer.score).label("total_manches"),
            func.count(
                case(
                    (
                        and_(
                            MatchPlayer.score > other_score_subquery.c.other_score,
                            other_score_subquery.c.match_id == MatchPlayer.match_id,
                            other_score_subquery.c.other_participant_id != MatchPlayer.participant_id,
                        ),
                        1,
                    )
                )
            ).label("wins"),
            case(
                (Participant.type == "player", User.name),
                else_=Participant.name,
            ).label("name"),
        )
        .join(Match, MatchPlayer.match_id == Match.id)
        .join(Participant, MatchPlayer.participant_id == Participant.id)
        .outerjoin(User, Participant.user_id == User.id)
        .outerjoin(
            other_score_subquery,
            and_(
                other_score_subquery.c.match_id == MatchPlayer.match_id,
                other_score_subquery.c.other_participant_id != MatchPlayer.participant_id,
            ),
        )
        .filter(Match.tournament_id == tournament_id, Match.status == "completed")
        .group_by(MatchPlayer.participant_id, "name")
        .order_by(desc("wins"), desc("total_manches"))
    )

    results = db.execute(leaderboard_query).fetchall()
    leaderboard = [
        TournamentLeaderboardEntry(
            participant_id=row.participant_id,
            name=row.name,
            wins=row.wins,
            total_manches=row.total_manches,
        )
        for row in results
    ]

    return TournamentLeaderboardResponse(tournament_id=tournament_id, leaderboard=leaderboard)


@leaderboards_router.get("/leaderboard/season/{season}", response_model=SeasonLeaderboardResponse)
def get_season_leaderboard(
    season: int,
    db: Session = Depends(get_users_db),
):
    tournament_ids = [
        t.id
        for t in db.query(Tournament).filter(
            func.extract("year", Tournament.start_date) == season
        ).all()
    ]
    if not tournament_ids:
        return SeasonLeaderboardResponse(season=str(season), leaderboard=[])

    other_score_subquery = (
        select(
            MatchPlayer.match_id,
            MatchPlayer.participant_id.label("other_participant_id"),
            MatchPlayer.score.label("other_score"),
        )
        .subquery()
    )

    single_query = (
        select(
            Participant.user_id.label("user_id"),
            (func.sum(MatchPlayer.score) + 
             func.count(
                 case(
                     (
                         and_(
                             MatchPlayer.score > other_score_subquery.c.other_score,
                             other_score_subquery.c.match_id == MatchPlayer.match_id,
                             other_score_subquery.c.other_participant_id != MatchPlayer.participant_id,
                         ),
                         1,
                     )
                 )
             )).label("total_points"),
            func.count(
                case(
                    (
                        and_(
                            MatchPlayer.score > other_score_subquery.c.other_score,
                            other_score_subquery.c.match_id == MatchPlayer.match_id,
                            other_score_subquery.c.other_participant_id != MatchPlayer.participant_id,
                        ),
                        literal(1.0),
                    )
                )
            ).label("single_wins"),
            func.sum(MatchPlayer.score).label("single_manches"),
            literal(0.0).label("double_wins"),
            literal(0.0).label("double_manches"),
            User.name,
        )
        .join(Match, MatchPlayer.match_id == Match.id)
        .join(Participant, MatchPlayer.participant_id == Participant.id)
        .join(User, Participant.user_id == User.id)
        .join(Tournament, Match.tournament_id == Tournament.id)
        .outerjoin(
            other_score_subquery,
            and_(
                other_score_subquery.c.match_id == MatchPlayer.match_id,
                other_score_subquery.c.other_participant_id != MatchPlayer.participant_id,
            ),
        )
        .filter(
            Match.tournament_id.in_(tournament_ids),
            Tournament.mode == "single",
            Participant.type == "player",
            Match.status == "completed",
        )
        .group_by(Participant.user_id, User.name)
    )

    team_score_subquery = (
        select(
            MatchPlayer.match_id,
            MatchPlayer.participant_id,
            func.sum(MatchPlayer.score).label("team_score"),
            func.count(
                case(
                    (
                        and_(
                            MatchPlayer.score > other_score_subquery.c.other_score,
                            other_score_subquery.c.match_id == MatchPlayer.match_id,
                            other_score_subquery.c.other_participant_id != MatchPlayer.participant_id,
                        ),
                        1,
                    )
                )
            ).label("team_wins")
        )
        .join(Match, MatchPlayer.match_id == Match.id)
        .join(Tournament, Match.tournament_id == Tournament.id)
        .outerjoin(
            other_score_subquery,
            and_(
                other_score_subquery.c.match_id == MatchPlayer.match_id,
                other_score_subquery.c.other_participant_id != MatchPlayer.participant_id,
            ),
        )
        .filter(
            Match.tournament_id.in_(tournament_ids),
            Tournament.mode == "double",
            Match.status == "completed",
        )
        .group_by(MatchPlayer.match_id, MatchPlayer.participant_id)
        .subquery()
    )

    double_query = (
        select(
            TeamMember.user_id.label("user_id"),
            (func.sum(team_score_subquery.c.team_score / 2.0) + 
             func.sum(team_score_subquery.c.team_wins * 0.5)).label("total_points"),
            literal(0.0).label("single_wins"),
            literal(0.0).label("single_manches"),
            func.sum(team_score_subquery.c.team_wins).label("double_wins"),
            func.sum(team_score_subquery.c.team_score).label("double_manches"),
            User.name,
        )
        .join(Participant, Participant.id == team_score_subquery.c.participant_id)
        .join(TeamMember, Participant.id == TeamMember.participant_id)
        .join(User, TeamMember.user_id == User.id)
        .filter(Participant.type == "team")
        .group_by(TeamMember.user_id, User.name)
    )

    union_query = union_all(single_query, double_query).alias("union_sub")

    final_query = (
        select(
            union_query.c.user_id,
            func.sum(union_query.c.total_points).label("total_points"),
            func.sum(union_query.c.single_wins).label("single_wins"),
            func.sum(union_query.c.double_wins).label("double_wins"),
            func.sum(union_query.c.single_manches).label("single_manches"),
            func.sum(union_query.c.double_manches).label("double_manches"),
            func.sum(union_query.c.single_wins + union_query.c.double_wins).label("wins"),
            func.sum(union_query.c.single_manches + union_query.c.double_manches).label("total_manches"),
            union_query.c.name,
        )
        .group_by(union_query.c.user_id, union_query.c.name)
        .order_by(desc("wins"), desc("total_manches"))
    )

    results = db.execute(final_query).fetchall()
    leaderboard = [
        LeaderboardEntry(
            user_id=row.user_id,
            name=row.name,
            total_points=float(row.total_points) or 0.0,
            single_wins=float(row.single_wins) or 0.0,
            double_wins=float(row.double_wins) or 0.0,
            single_manches=float(row.single_manches) or 0.0,
            double_manches=float(row.double_manches) or 0.0,
        )
        for row in results
    ]

    return SeasonLeaderboardResponse(season=str(season), leaderboard=leaderboard)

@leaderboards_router.get("/{tournament_id}/pools-leaderboard", response_model=List[PoolLeaderboardResponse])
def get_pools_leaderboard(
    tournament_id: int,
    db: Session = Depends(get_users_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    pools = db.query(Pool).filter(Pool.tournament_id == tournament_id).all()
    response = []
    for pool in pools:
        other_score_subquery = (
            select(
                MatchPlayer.match_id,
                MatchPlayer.participant_id.label("other_participant_id"),
                MatchPlayer.score.label("other_score"),
            )
            .subquery()
        )

        leaderboard_query = (
            select(
                MatchPlayer.participant_id,
                func.sum(MatchPlayer.score).label("total_manches"),
                func.count(
                    case(
                        (
                            and_(
                                MatchPlayer.score > other_score_subquery.c.other_score,
                                other_score_subquery.c.match_id == MatchPlayer.match_id,
                                other_score_subquery.c.other_participant_id != MatchPlayer.participant_id,
                            ),
                            1,
                        )
                    )
                ).label("wins"),
                case(
                    (Participant.type == "player", User.name),
                    else_=Participant.name,
                ).label("name"),
            )
            .join(Match, MatchPlayer.match_id == Match.id)
            .join(Participant, MatchPlayer.participant_id == Participant.id)
            .outerjoin(User, Participant.user_id == User.id)
            .outerjoin(
                other_score_subquery,
                and_(
                    other_score_subquery.c.match_id == MatchPlayer.match_id,
                    other_score_subquery.c.other_participant_id != MatchPlayer.participant_id,
                ),
            )
            .filter(Match.pool_id == pool.id, Match.status == "completed")
            .group_by(MatchPlayer.participant_id, "name")
            .order_by(desc("wins"), desc("total_manches"))
        )

        results = db.execute(leaderboard_query).fetchall()
        leaderboard = [
            TournamentLeaderboardEntry(
                participant_id=row.participant_id,
                name=row.name,
                wins=row.wins,
                total_manches=row.total_manches,
            )
            for row in results
        ]

        response.append(
            PoolLeaderboardResponse(
                tournament_id=tournament_id,
                pool_id=pool.id,
                pool_name=pool.name,
                leaderboard=leaderboard,
            )
        )

    return response