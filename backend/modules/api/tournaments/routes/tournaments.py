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
    "/",
    response_model=TournamentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tournament",
    description="Creates a new tournament with the provided details. Requires admin or editor privileges."
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


@tournaments_router.delete(
    "/{tournament_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tournament",
    description="Deletes a tournament and all associated data (pools, matches, participants). Requires admin or editor privileges."
)
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
    "/{tournament_id}",
    response_model=TournamentResponse,
    summary="Update a tournament",
    description="Updates a tournament's details. Cannot set a tournament to 'running' if already running. Requires admin or editor privileges."
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


@tournaments_router.get(
    "/{tournament_id}",
    response_model=TournamentResponse,
    summary="Get a tournament by ID",
    description="Retrieves details of a specific tournament by its ID."
)
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


@tournaments_router.get(
    "/",
    response_model=List[TournamentResponse],
    summary="List all tournaments",
    description="Retrieves a list of all tournaments in the system."
)
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


@tournaments_router.post(
    "/registrations/",
    response_model=TournamentRegistrationResponse,
    summary="Register a user to a tournament",
    description="Registers a user to an open tournament. Creates a Participant of type 'player' if the tournament is in 'single' mode. Prevents duplicate registrations."
)
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

    # Create a Participant of type 'player' if the tournament is in 'single' mode
    if tournament.mode == "single":
        existing_participant = db.query(Participant).filter(
            Participant.tournament_id == registration_data.tournament_id,
            Participant.user_id == current_user.id,
            Participant.type == "player"
        ).first()
        if not existing_participant:
            new_participant = Participant(
                tournament_id=registration_data.tournament_id,
                type="player",
                user_id=current_user.id,
                name=db.query(User).filter(User.id == current_user.id).first().name
            )
            db.add(new_participant)
            db.commit()
            db.refresh(new_participant)

    return TournamentRegistrationResponse(
        id=new_registration.id,
        user_id=new_registration.user_id,
        tournament_id=new_registration.tournament_id,
        registration_date=new_registration.registration_date,
    )


@tournaments_router.post(
    "/register-player",
    response_model=TournamentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_new_player(
    player_data: TournamentRegistrationCreate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    # Check if tournament exists
    tournament = (
        db.query(Tournament).filter(Tournament.id == player_data.tournament_id).first()
    )
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != "open":
        raise HTTPException(
            status_code=400, detail="Registrations are closed for this tournament"
        )

    # Register the user for the tournament
    new_registration = TournamentRegistration(
        user_id=player_data.user_id,
        tournament_id=player_data.tournament_id,
    )
    db.add(new_registration)
    db.commit()
    db.refresh(new_registration)

    # Create a Participant of type 'player' if the tournament is in 'single' mode
    if tournament.mode == "single":
        existing_participant = db.query(Participant).filter(
            Participant.tournament_id == player_data.tournament_id,
            Participant.user_id == player_data.user_id,
            Participant.type == "player"
        ).first()
        if not existing_participant:
            new_participant = Participant(
                tournament_id=player_data.tournament_id,
                type="player",
                user_id=player_data.user_id,
                name=db.query(User).filter(User.id == player_data.user_id,).first().name
            )
            db.add(new_participant)
            db.commit()
            db.refresh(new_participant)

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


@tournaments_router.get("/{tournament_id}/registered-users", response_model=List[dict])
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
    
    response = []
    for user in users:
        team_member = (
            db.query(TeamMember)
            .join(Participant, TeamMember.participant_id == Participant.id)
            .filter(
                TeamMember.user_id == user.id,
                Participant.tournament_id == tournament_id,
                Participant.type == "team"
            )
            .first()
        )
        team = db.query(Participant).filter(
            Participant.id == team_member.participant_id,
            Participant.tournament_id == tournament_id,
            Participant.type == "team"
        ).first() if team_member else None
        response.append({
            "id": user.id,
            "name": user.name,
            "team_id": team.id if team else None,
            "team_name": team.name if team else None
        })
    return response

@tournaments_router.post(
    "/{tournament_id}/teams",
    response_model=ParticipantResponse,
    summary="Create a team for a tournament",
    description="Creates a team of two registered players for a tournament. Checks for valid registrations and prevents duplicate team memberships."
)
def create_team(
    tournament_id: int,
    team_data: TeamCreate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    if team_data.player1_id == team_data.player2_id:
        raise HTTPException(status_code=400, detail="Players in a team must be different")

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

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

    existing_team1 = (
        db.query(TeamMember)
        .join(Participant, TeamMember.participant_id == Participant.id)
        .filter(TeamMember.user_id == team_data.player1_id, Participant.tournament_id == tournament_id)
        .first()
    )
    existing_team2 = (
        db.query(TeamMember)
        .join(Participant, TeamMember.participant_id == Participant.id)
        .filter(TeamMember.user_id == team_data.player2_id, Participant.tournament_id == tournament_id)
        .first()
    )
    if existing_team1 or existing_team2:
        raise HTTPException(status_code=400, detail="One or both players are already in a team for this tournament")

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


@tournaments_router.delete("/{tournament_id}/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    tournament_id: int,
    team_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(status_code=403, detail="Access denied")

    team = db.query(Participant).filter(
        Participant.id == team_id,
        Participant.tournament_id == tournament_id,
        Participant.type == "team"
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Delete team members
    db.execute(delete(TeamMember).where(TeamMember.participant_id == team_id))
    
    # Delete team from matches
    db.execute(
        delete(MatchPlayer).where(
            MatchPlayer.match_id.in_(
                select(Match.id).where(Match.tournament_id == tournament_id)
            ),
            MatchPlayer.participant_id == team_id
        )
    )
    
    # Delete team from pools
    db.execute(
        delete(pool_participant_association).where(
            pool_participant_association.c.participant_id == team_id
        )
    )
    
    # Delete the team
    db.delete(team)
    db.commit()

@tournaments_router.delete("/registrations/user/{user_id}/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
def unregister_user(
    user_id: int,
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(status_code=403, detail="Access denied")

    registration = db.query(TournamentRegistration).filter(
        TournamentRegistration.user_id == user_id,
        TournamentRegistration.tournament_id == tournament_id
    ).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Remove user from any team
    team_member = db.query(TeamMember).filter(TeamMember.user_id == user_id).first()
    if team_member:
        team = db.query(Participant).filter(
            Participant.id == team_member.participant_id,
            Participant.tournament_id == tournament_id,
            Participant.type == "team"
        ).first()
        if team:
            db.execute(delete(TeamMember).where(TeamMember.participant_id == team.id))
            db.execute(
                delete(MatchPlayer).where(
                    MatchPlayer.match_id.in_(
                        select(Match.id).where(Match.tournament_id == tournament_id)
                    ),
                    MatchPlayer.participant_id == team.id
                )
            )
            db.execute(
                delete(pool_participant_association).where(
                    pool_participant_association.c.participant_id == team.id
                )
            )
            db.delete(team)

    # Remove player participant if exists
    participant = db.query(Participant).filter(
        Participant.tournament_id == tournament_id,
        Participant.user_id == user_id,
        Participant.type == "player"
    ).first()
    if participant:
        db.delete(participant)

    db.delete(registration)
    db.commit()


@tournaments_router.get(
    "/{tournament_id}/participants",
    response_model=List[ParticipantResponse],
    summary="List participants of a tournament",
    description="Retrieves all participants (players or teams) for a specific tournament. Requires admin or editor privileges."
)
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


@tournaments_router.post(
    "/{tournament_id}/reset",
    summary="Reset a tournament",
    description="Resets a tournament by deleting all associated matches, pools, and participants, and setting status to 'open'. Requires admin or editor privileges."
)
def reset_tournament(tournament_id: int, db: Session = Depends(get_users_db)):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    db.execute(
        delete(MatchPlayer).where(
            MatchPlayer.match_id.in_(
                select(Match.id).where(Match.tournament_id == tournament_id)
            )
        )
    )

    db.execute(delete(Match).where(Match.tournament_id == tournament_id))

    pool_ids = [pool.id for pool in db.query(Pool).filter(Pool.tournament_id == tournament_id).all()]
    if pool_ids:
        db.execute(
            delete(pool_participant_association).where(
                pool_participant_association.c.pool_id.in_(pool_ids)
            )
        )

    db.execute(delete(Pool).where(Pool.tournament_id == tournament_id))

    tournament.status = "open"
    tournament.type = None
    db.commit()

    return {"reset": True}


@tournaments_router.get(
    "/{tournament_id}/details",
    response_model=TournamentFullDetailSchema,
    summary="Get full tournament details",
    description="Retrieves detailed information about a tournament, including pools, participants, and matches."
)
def get_full_tournament_details(
    tournament_id: int, db: Session = Depends(get_users_db)
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found.")
    pools = db.query(Pool).filter(Pool.tournament_id == tournament_id).all()
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