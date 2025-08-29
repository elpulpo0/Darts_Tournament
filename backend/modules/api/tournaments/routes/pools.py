from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from modules.database.dependencies import get_users_db
from modules.api.tournaments.models import Pool, Participant, Tournament
from modules.api.tournaments.schemas import PoolResponse, PoolCreate, MatchResponse, PlayerResponse, ParticipantResponse
from typing import List

pools_router = APIRouter(prefix="/tournaments", tags=["pools"])


@pools_router.post("/{tournament_id}/pools", response_model=PoolResponse)
def create_pool(
    tournament_id: int,
    pool_data: PoolCreate,
    db: Session = Depends(get_users_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    new_pool = Pool(tournament_id=tournament_id, name=pool_data.name)
    db.add(new_pool)
    db.commit()
    db.refresh(new_pool)

    # Associer les participants à la poule
    for participant_id in pool_data.participant_ids:
        participant = db.query(Participant).filter(Participant.id == participant_id).first()
        if not participant:
            raise HTTPException(status_code=404, detail=f"Participant {participant_id} not found")
        new_pool.participants.append(participant)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Integrity error: participant already in this pool or other DB issue.",
        )

    return PoolResponse(
        id=new_pool.id,
        participants=[ParticipantResponse(id=p.id, type=p.type, name=p.name or p.user.name, users=[]) for p in new_pool.participants],  # Simplified, adjust as needed
        matches=[],
    )


@pools_router.get(
    "/{tournament_id}/pools",
    response_model=List[PoolResponse],
    summary="Get all pools for a tournament",
)
def get_tournament_pools(tournament_id: int, db: Session = Depends(get_users_db)):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    pools = db.query(Pool).filter(Pool.tournament_id == tournament_id).all()
    response = []
    for pool in pools:
        participants = []
        for p in pool.participants:
            if p.type == 'player':
                name = p.user.name if p.user else ''
                users = [PlayerResponse(id=p.user.id, name=name)] if p.user else []
            else:
                name = p.name
                users = [PlayerResponse(id=m.user.id, name=m.user.name) for m in p.team_members]
            participants.append(ParticipantResponse(id=p.id, type=p.type, name=name, users=users))
        matches = []
        for m in pool.matches:
            match_participants = []
            for mp in m.match_participations:
                p = mp.participant
                name = p.user.name if p.type == 'player' else p.name
                match_participants.append({"participant_id": p.id, "name": name, "score": mp.score})
            matches.append(
                MatchResponse(
                    id=m.id,
                    tournament_id=m.tournament_id,
                    status=m.status,
                    participants=match_participants,
                    pool_id=m.pool_id,
                    round=m.round,
                )
            )
        response.append(PoolResponse(id=pool.id, participants=participants, matches=matches))
    return response