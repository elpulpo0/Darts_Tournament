from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from modules.database.dependencies import get_users_db
from modules.api.tournaments.models import Tournament, TournamentRegistration, Participant, TeamMember, Match, MatchPlayer, Pool, pool_participant_association
from modules.api.tournaments.schemas import (
    TournamentCreate,
    TournamentUpdate,
    TournamentResponse,
    TournamentRegistrationCreate,
    TournamentRegistrationResponse,
    ParticipantResponse,
    TeamCreate,
    PlayerResponse,
    TournamentFullDetailSchema
)
from modules.api.users.functions import get_current_user
from modules.api.users.models import User
from modules.api.users.schemas import TokenData
from typing import List

tournaments_router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@tournaments_router.post(
    "/", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED
)
def create_tournament(
    tournament_data: TournamentCreate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )
    new_tournament = Tournament(
        name=tournament_data.name,
        description=tournament_data.description,
        start_date=tournament_data.start_date,
        is_active=tournament_data.is_active,
        type=tournament_data.type,
        mode=tournament_data.mode,
        status=tournament_data.status,
    )
    db.add(new_tournament)
    db.commit()
    db.refresh(new_tournament)
    return TournamentResponse(
        id=new_tournament.id,
        name=new_tournament.name,
        description=new_tournament.description,
        start_date=new_tournament.start_date,
        is_active=new_tournament.is_active,
        type=new_tournament.type,
        mode=new_tournament.mode,
        status=new_tournament.status,
    )


@tournaments_router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found.")

    db.delete(tournament)
    db.commit()


@tournaments_router.patch(
    "/{tournament_id}", response_model=TournamentResponse, summary="Update tournament"
)
def update_tournament(
    tournament_id: int,
    tournament_data: TournamentUpdate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if "admin" not in current_user.scopes and "editor" not in current_user.scopes:
        raise HTTPException(
            status_code=403,
            detail="Access denied: administrators or editors only.",
        )

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament_data.status == "running" and tournament.status == "running":
        raise HTTPException(status_code=400, detail="Tournament already running")

    if tournament_data.name is not None:
        tournament.name = tournament_data.name
    if tournament_data.description is not None:
        tournament.description = tournament_data.description
    if tournament_data.start_date is not None:
        tournament.start_date = tournament_data.start_date
    if tournament_data.is_active is not None:
        tournament.is_active = tournament_data.is_active
    if tournament_data.type is not None:
        tournament.type = tournament_data.type
    if tournament_data.mode is not None:
        tournament.mode = tournament_data.mode
    if tournament_data.status is not None:
        if tournament_data.status not in ["open", "running", "closed"]:
            raise HTTPException(status_code=400, detail="Invalid status value")
        tournament.status = tournament_data.status

    db.commit()
    db.refresh(tournament)

    return TournamentResponse(
        id=tournament.id,
        name=tournament.name,
        description=tournament.description,
        start_date=tournament.start_date,
        is_active=tournament.is_active,
        type=tournament.type,
        mode=tournament.mode,
        status=tournament.status,
    )


@tournaments_router.get("/{tournament_id}", response_model=TournamentResponse)
def get_tournament(
    tournament_id: int,
    db: Session = Depends(get_users_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return TournamentResponse(
        id=tournament.id,
        name=tournament.name,
        description=tournament.description,
        start_date=tournament.start_date,
        is_active=tournament.is_active,
        type=tournament.type,
        mode=tournament.mode,
        status=tournament.status,
    )


@tournaments_router.get("/", response_model=List[TournamentResponse])
def get_tournaments(
    db: Session = Depends(get_users_db),
):
    tournaments = db.query(Tournament).all()
    return [
        TournamentResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            start_date=t.start_date,
            is_active=t.is_active,
            type=t.type,
            mode=t.mode,
            status=t.status,
        )
        for t in tournaments
    ]


@tournaments_router.post("/registrations/", response_model=TournamentRegistrationResponse)
def register_to_tournament(
    registration_data: TournamentRegistrationCreate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    tournament = db.query(Tournament).filter(Tournament.id == registration_data.tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament.status != "open":
        raise HTTPException(status_code=400, detail="Registrations are closed for this tournament")

    existing_registration = db.query(TournamentRegistration).filter(
        TournamentRegistration.user_id == current_user.id,
        TournamentRegistration.tournament_id == registration_data.tournament_id,
    ).first()
    if existing_registration:
        raise HTTPException(status_code=400, detail="You are already registered for this tournament")

    new_registration = TournamentRegistration(
        user_id=current_user.id,
        tournament_id=registration_data.tournament_id,
    )
    db.add(new_registration)
    db.commit()
    db.refresh(new_registration)
    return TournamentRegistrationResponse(
        id=new_registration.id,
        user_id=new_registration.user_id,
        tournament_id=new_registration.tournament_id,
        registration_date=new_registration.registration_date,
    )


@tournaments_router.delete("/registrations/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
def unregister_from_tournament(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    registration = db.query(TournamentRegistration).filter(
        TournamentRegistration.user_id == current_user.id,
        TournamentRegistration.tournament_id == tournament_id,
    ).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    db.delete(registration)
    db.commit()


@tournaments_router.get("/{tournament_id}/my-registration", response_model=bool)
def check_my_registration(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    registration = db.query(TournamentRegistration).filter(
        TournamentRegistration.user_id == current_user.id,
        TournamentRegistration.tournament_id == tournament_id,
    ).first()
    return registration is not None


@tournaments_router.get("/{tournament_id}/registered-users", response_model=List[PlayerResponse])
def get_registered_users(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(status_code=403, detail="Access denied")

    registrations = db.query(TournamentRegistration).filter(
        TournamentRegistration.tournament_id == tournament_id
    ).all()
    user_ids = [reg.user_id for reg in registrations]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    return [PlayerResponse(id=u.id, name=u.name) for u in users]


@tournaments_router.post("/{tournament_id}/teams", response_model=ParticipantResponse)
def create_team(
    tournament_id: int,
    team_data: TeamCreate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(status_code=403, detail="Access denied")

    if team_data.player1_id == team_data.player2_id:
        raise HTTPException(status_code=400, detail="Players in a team must be different")

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament.mode != "double":
        raise HTTPException(status_code=400, detail="Teams can only be created for double mode tournaments")

    # Check if players are registered
    reg1 = db.query(TournamentRegistration).filter(
        TournamentRegistration.user_id == team_data.player1_id,
        TournamentRegistration.tournament_id == tournament_id
    ).first()
    reg2 = db.query(TournamentRegistration).filter(
        TournamentRegistration.user_id == team_data.player2_id,
        TournamentRegistration.tournament_id == tournament_id
    ).first()
    if not reg1 or not reg2:
        raise HTTPException(status_code=400, detail="Both players must be registered to the tournament")

    # Check if players are already in a team
    existing_team1 = db.query(TeamMember).filter(TeamMember.user_id == team_data.player1_id).first()
    existing_team2 = db.query(TeamMember).filter(TeamMember.user_id == team_data.player2_id).first()
    if existing_team1 or existing_team2:
        raise HTTPException(status_code=400, detail="One or both players are already in a team")

    new_participant = Participant(
        tournament_id=tournament_id,
        type="team",
        name=team_data.name,
    )
    db.add(new_participant)
    db.commit()
    db.refresh(new_participant)

    team_member1 = TeamMember(participant_id=new_participant.id, user_id=team_data.player1_id)
    team_member2 = TeamMember(participant_id=new_participant.id, user_id=team_data.player2_id)
    db.add(team_member1)
    db.add(team_member2)
    db.commit()

    users = db.query(User).filter(User.id.in_([team_data.player1_id, team_data.player2_id])).all()
    user_responses = [PlayerResponse(id=u.id, name=u.name) for u in users]

    return ParticipantResponse(
        id=new_participant.id,
        type="team",
        name=new_participant.name,
        users=user_responses,
    )


@tournaments_router.get("/{tournament_id}/participants", response_model=List[ParticipantResponse])
def get_participants(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(status_code=403, detail="Access denied")

    participants = db.query(Participant).filter(Participant.tournament_id == tournament_id).all()
    response = []
    for p in participants:
        if p.type == "player":
            if not p.user:
                continue
            name = p.user.name
            users = [PlayerResponse(id=p.user.id, name=p.user.name)]
        else:
            name = p.name
            users = [PlayerResponse(id=m.user.id, name=m.user.name) for m in p.team_members]
        response.append(ParticipantResponse(id=p.id, type=p.type, name=name, users=users))
    return response


@tournaments_router.post("/{tournament_id}/reset")
def reset_tournament(tournament_id: int, db: Session = Depends(get_users_db)):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Supprimer explicitement les enregistrements de match_players
    db.execute(
        delete(MatchPlayer).where(
            MatchPlayer.match_id.in_(
                select(Match.id).where(Match.tournament_id == tournament_id)
            )
        )
    )

    # Supprimer tous les matchs du tournoi
    db.execute(delete(Match).where(Match.tournament_id == tournament_id))

    # Supprimer les associations participant-poule
    pool_ids = [pool.id for pool in db.query(Pool).filter(Pool.tournament_id == tournament_id).all()]
    if pool_ids:
        db.execute(
            delete(pool_participant_association).where(
                pool_participant_association.c.pool_id.in_(pool_ids)
            )
        )

    # Supprimer toutes les poules du tournoi
    db.execute(delete(Pool).where(Pool.tournament_id == tournament_id))

    # Supprimer les team_members et participants
    participant_ids = [p.id for p in db.query(Participant).filter(Participant.tournament_id == tournament_id).all()]
    if participant_ids:
        db.execute(delete(TeamMember).where(TeamMember.participant_id.in_(participant_ids)))
    db.execute(delete(Participant).where(Participant.tournament_id == tournament_id))

    # Réinitialiser le statut, type et mode du tournoi
    tournament.status = "open"
    tournament.type = None
    tournament.mode = None
    db.commit()

    return {"reset": True}


@tournaments_router.get(
    "/{tournament_id}/details", response_model=TournamentFullDetailSchema
)
def get_full_tournament_details(
    tournament_id: int, db: Session = Depends(get_users_db)
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found.")
    # pools avec participants :
    pools = db.query(Pool).filter(Pool.tournament_id == tournament_id).all()
    # On regroupe les matches par pool
    pool_dicts = []
    for pool in pools:
        pool_matches = db.query(Match).filter(Match.pool_id == pool.id).all()
        pool_participants = []
        for p in pool.participants:
            name = p.user.name if p.type == 'player' else p.name
            pool_participants.append({"id": p.id, "name": name})
        pool_matches_dict = []
        for m in pool_matches:
            match_participants = []
            for mp in m.match_participations:
                p = mp.participant
                name = p.user.name if p.type == 'player' else p.name
                match_participants.append(
                    {
                        "id": p.id,
                        "name": name,
                        "score": mp.score,
                    }
                )
            pool_matches_dict.append(
                {
                    "id": m.id,
                    "participants": match_participants,
                    "status": m.status,
                    "pool_id": m.pool_id,
                    "round": m.round,
                }
            )
        pool_dicts.append(
            {
                "id": pool.id,
                "name": pool.name,
                "participants": pool_participants,
                "matches": pool_matches_dict,
            }
        )
    # Phase finale : tous les matches sans pool_id
    finals_matches = (
        db.query(Match)
        .filter(Match.tournament_id == tournament_id)
        .filter(Match.pool_id.is_(None))
        .all()
    )
    finals_matches_dict = []
    for m in finals_matches:
        match_participants = []
        for mp in m.match_participations:
            p = mp.participant
            name = p.user.name if p.type == 'player' else p.name
            match_participants.append(
                {
                    "id": p.id,
                    "name": name,
                    "score": mp.score,
                }
            )
        finals_matches_dict.append(
            {
                "id": m.id,
                "participants": match_participants,
                "status": m.status,
                "round": m.round,
            }
        )

    return {
        "id": tournament.id,
        "name": tournament.name,
        "type": tournament.type,
        "mode": tournament.mode,
        "status": tournament.status,
        "pools": pool_dicts,
        "final_matches": finals_matches_dict,
    }