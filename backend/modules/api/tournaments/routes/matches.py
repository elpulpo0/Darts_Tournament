from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from modules.database.dependencies import get_users_db
from modules.api.tournaments.models import Match, MatchPlayer, Participant, Tournament
from modules.api.tournaments.schemas import MatchCreate, MatchUpdate, MatchResponse
from typing import List

matches_router = APIRouter(prefix="/tournaments", tags=["Matches"])


@matches_router.post("/matches/", response_model=MatchResponse)
def create_match(
    match_data: MatchCreate,
    db: Session = Depends(get_users_db),
):
    tournament = (
        db.query(Tournament).filter(Tournament.id == match_data.tournament_id).first()
    )
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    new_match = Match(
        tournament_id=match_data.tournament_id,
        status=match_data.status,
        pool_id=match_data.pool_id,
        round=match_data.round,
    )
    db.add(new_match)
    db.commit()
    db.refresh(new_match)

    # Associer les participants au match via MatchPlayer
    participants_list = []
    for participant_id in match_data.participant_ids:
        participant = (
            db.query(Participant).filter(Participant.id == participant_id).first()
        )
        if not participant:
            raise HTTPException(
                status_code=404, detail=f"Participant {participant_id} not found"
            )
        match_player = MatchPlayer(
            match_id=new_match.id, participant_id=participant_id, score=None
        )
        db.add(match_player)
        name = participant.name or (
            participant.members[0].user.name if participant.members else "Inconnu"
        )
        participants_list.append(
            {"participant_id": participant_id, "name": name, "score": None}
        )

    db.commit()

    return MatchResponse(
        id=new_match.id,
        tournament_id=new_match.tournament_id,
        status=new_match.status,
        participants=participants_list,
        pool_id=new_match.pool_id,
        round=new_match.round,
    )


@matches_router.get(
    "/matches/tournament/{tournament_id}", response_model=List[MatchResponse]
)
def get_tournament_matches(
    tournament_id: int,
    db: Session = Depends(get_users_db),
):
    matches = db.query(Match).filter(Match.tournament_id == tournament_id).all()
    response = []
    for match in matches:
        participants_list = []
        for mp in match.match_participations:
            p = mp.participant
            name = p.name or (p.members[0].user.name if p.members else "Inconnu")
            participants_list.append(
                {"participant_id": p.id, "name": name, "score": mp.score}
            )
        response.append(
            MatchResponse(
                id=match.id,
                tournament_id=match.tournament_id,
                status=match.status,
                participants=participants_list,
                pool_id=match.pool_id,
                round=match.round,
            )
        )
    return response


@matches_router.patch("/matches/{match_id}", response_model=MatchResponse)
def update_match(
    match_id: int,
    match_data: MatchUpdate,
    db: Session = Depends(get_users_db),
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    if match_data.status is not None:
        match.status = match_data.status

    participants_list = []
    if match_data.scores:
        for score_entry in match_data.scores:
            participant_id = score_entry.get("participant_id")
            score = score_entry.get("score")
            match_player = (
                db.query(MatchPlayer)
                .filter(
                    MatchPlayer.match_id == match_id,
                    MatchPlayer.participant_id == participant_id,
                )
                .first()
            )
            if not match_player:
                raise HTTPException(
                    status_code=404,
                    detail=f"Participant {participant_id} not found in match",
                )
            match_player.score = score
            p = match_player.participant
            name = p.name or (p.members[0].user.name if p.members else "Inconnu")
            participants_list.append(
                {"participant_id": participant_id, "name": name, "score": score}
            )

    db.commit()
    db.refresh(match)

    if not participants_list:
        for mp in match.match_participations:
            p = mp.participant
            name = p.name or (p.members[0].user.name if p.members else "Inconnu")
            participants_list.append(
                {"participant_id": p.id, "name": name, "score": mp.score}
            )

    return MatchResponse(
        id=match.id,
        tournament_id=match.tournament_id,
        status=match.status,
        participants=participants_list,
        pool_id=match.pool_id,
        round=match.round,
    )


@matches_router.post("/matches/{match_id}/cancel", response_model=MatchResponse)
def cancel_match_scores(
    match_id: int,
    db: Session = Depends(get_users_db),
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Reset match status to 'pending'
    match.status = "pending"

    # Reset scores to null for all participants
    participants_list = []
    for match_player in match.match_participations:
        match_player.score = None
        p = match_player.participant
        name = p.name or (p.members[0].user.name if p.members else "Inconnu")
        participants_list.append({"participant_id": p.id, "name": name, "score": None})

    db.commit()
    db.refresh(match)

    return MatchResponse(
        id=match.id,
        tournament_id=match.tournament_id,
        status=match.status,
        participants=participants_list,
        pool_id=match.pool_id,
        round=match.round,
    )


@matches_router.delete("/matches/{match_id}", status_code=204)
def delete_match(
    match_id: int,
    db: Session = Depends(get_users_db),
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Supprimer les entrées liées dans MatchPlayer
    db.query(MatchPlayer).filter(MatchPlayer.match_id == match_id).delete()
    db.delete(match)
    db.commit()
    return None
