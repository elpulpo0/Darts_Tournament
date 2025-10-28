from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from modules.database.dependencies import get_users_db
from modules.api.tournaments.models import (
    Tournament,
    TournamentRegistration,
    Participant,
    ParticipantMember,
    Match,
    MatchPlayer,
    Pool,
    pool_participant_association,
)
from modules.api.tournaments.schemas import (
    TournamentCreate,
    TournamentUpdate,
    TournamentResponse,
    TournamentRegistrationCreate,
    TournamentRegistrationResponse,
    ParticipantCreate,
    ParticipantResponse,
    PlayerResponse,
    TournamentFullDetailSchema,
    SwapPlayersRequest,
)
from modules.api.users.functions import get_current_user
from modules.api.users.models import User
from modules.api.users.schemas import TokenData
from typing import List
from datetime import datetime, UTC
from modules.api.users.telegram import notify_telegram, NotifyUserRegistration
import os

tournaments_router = APIRouter(prefix="/tournaments", tags=["Tournaments"])


@tournaments_router.post(
    "/",
    response_model=TournamentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tournament",
    description="Creates a new tournament with the provided details. Requires admin or editor privileges.",
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
    description="Deletes a tournament and all associated data (pools, matches, participants). Requires admin or editor privileges.",
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
    description="Updates a tournament's details. Resets participants if mode changes. Requires admin or editor privileges.",
)
def update_tournament(
    tournament_id: int,
    tournament_data: TournamentUpdate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament_data.status == "running" and tournament.status == "running":
        raise HTTPException(status_code=400, detail="Tournament already running")

    # Check if mode is changing
    if tournament_data.mode and tournament_data.mode != tournament.mode:
        # Reset participants
        db.execute(
            delete(ParticipantMember).where(
                ParticipantMember.participant_id.in_(
                    select(Participant.id).where(
                        Participant.tournament_id == tournament_id
                    )
                )
            )
        )
        db.execute(
            delete(MatchPlayer).where(
                MatchPlayer.match_id.in_(
                    select(Match.id).where(Match.tournament_id == tournament_id)
                )
            )
        )
        db.execute(
            delete(pool_participant_association).where(
                pool_participant_association.c.participant_id.in_(
                    select(Participant.id).where(
                        Participant.tournament_id == tournament_id
                    )
                )
            )
        )
        db.execute(
            delete(Participant).where(Participant.tournament_id == tournament_id)
        )

    # Update tournament fields
    for field, value in tournament_data.dict(exclude_unset=True).items():
        setattr(tournament, field, value)

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
    description="Retrieves details of a specific tournament by its ID.",
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
    description="Retrieves a list of all tournaments in the system.",
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
    summary="Register user(s) to a tournament",
    description="Registers a single user or a team to a tournament. For single mode, creates a participant without a name. For double mode, creates a team with a custom name.",
)
def register_to_tournament(
    registration_data: TournamentRegistrationCreate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    tournament = (
        db.query(Tournament)
        .filter(Tournament.id == registration_data.tournament_id)
        .first()
    )
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != "open":
        raise HTTPException(
            status_code=400, detail="Tournament is not open for registration"
        )

    user_ids = []
    participant_name = None
    create_participant = False

    if registration_data.user_id:  # Single player registration
        user_id = registration_data.user_id or current_user.id
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        user_ids = [user_id]
        participant_name = None  # Explicitly set no name for single mode
        create_participant = (
            tournament.mode == "single"
        )  # Create participant for single mode
    elif registration_data.user_ids:  # Team creation (double mode only)
        if tournament.mode != "double":
            raise HTTPException(
                status_code=400, detail="Team creation is only allowed in double mode"
            )
        if len(registration_data.user_ids) != 2:
            raise HTTPException(
                status_code=400, detail="Exactly 2 user IDs required for team creation"
            )
        if not registration_data.name:
            raise HTTPException(
                status_code=400, detail="Team name required for team creation"
            )
        for user_id in registration_data.user_ids:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        user_ids = registration_data.user_ids
        participant_name = registration_data.name
        create_participant = True
    else:
        raise HTTPException(status_code=400, detail="Must provide user_id or user_ids")

    # Check for existing registrations
    for user_id in user_ids:
        existing_registration = (
            db.query(TournamentRegistration)
            .filter(
                TournamentRegistration.tournament_id == registration_data.tournament_id,
                TournamentRegistration.user_id == user_id,
            )
            .first()
        )
        if existing_registration:
            raise HTTPException(
                status_code=400, detail=f"User {user_id} already registered"
            )

    # Create participant if required
    participant = None
    if create_participant:
        participant = Participant(
            tournament_id=registration_data.tournament_id,
            name=participant_name,  # Will be None for single mode
        )
        db.add(participant)
        db.commit()
        db.refresh(participant)

    # Register users
    for user_id in user_ids:
        registration = TournamentRegistration(
            user_id=user_id,
            tournament_id=registration_data.tournament_id,
            registration_date=datetime.now(UTC),
        )
        db.add(registration)
        if participant:
            member = ParticipantMember(participant_id=participant.id, user_id=user_id)
            db.add(member)

    db.commit()

    first_registration = (
        db.query(TournamentRegistration)
        .filter(
            TournamentRegistration.tournament_id == registration_data.tournament_id,
            TournamentRegistration.user_id == user_ids[0],
        )
        .first()
    )

    if not os.getenv("TEST_MODE") and os.getenv("ENV") != "dev":
        notify_user = NotifyUserRegistration(
            nickname=user.nickname,
            tournamentName=tournament.name,
            type="userRegister",
        )
    notify_telegram(notify_user)

    return TournamentRegistrationResponse(
        id=first_registration.id,
        user_id=user_ids[0],
        tournament_id=registration_data.tournament_id,
        registration_date=first_registration.registration_date,
    )


@tournaments_router.post(
    "/register-player",
    response_model=TournamentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a player or team (admin only)",
    description="Registers a single player or team to a tournament. For single mode, creates a participant without a name. For double mode, creates a team with a custom name. Requires admin or editor privileges.",
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

    tournament = (
        db.query(Tournament).filter(Tournament.id == player_data.tournament_id).first()
    )
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != "open":
        raise HTTPException(
            status_code=400, detail="Registrations are closed for this tournament"
        )

    user_ids = []
    participant_name = None
    create_participant = False

    if player_data.user_id:  # Single player registration
        user_id = player_data.user_id
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        user_ids = [user_id]
        participant_name = None  # Explicitly set no name for single mode
        create_participant = (
            tournament.mode == "single"
        )  # Create participant for single mode
    elif player_data.user_ids:  # Team creation (double mode only)
        if tournament.mode != "double":
            raise HTTPException(
                status_code=400, detail="Team creation is only allowed in double mode"
            )
        if len(player_data.user_ids) != 2:
            raise HTTPException(
                status_code=400, detail="Exactly 2 user IDs required for team creation"
            )
        if not player_data.name:
            raise HTTPException(
                status_code=400, detail="Team name required for team creation"
            )
        for user_id in player_data.user_ids:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        user_ids = player_data.user_ids
        participant_name = player_data.name
        create_participant = True
    else:
        raise HTTPException(status_code=400, detail="Must provide user_id or user_ids")

    # Check for existing registrations
    for user_id in user_ids:
        existing_registration = (
            db.query(TournamentRegistration)
            .filter(
                TournamentRegistration.tournament_id == player_data.tournament_id,
                TournamentRegistration.user_id == user_id,
            )
            .first()
        )
        if existing_registration:
            raise HTTPException(
                status_code=400, detail=f"User {user_id} already registered"
            )

    # Create participant if required
    participant = None
    if create_participant:
        participant = Participant(
            tournament_id=player_data.tournament_id,
            name=participant_name,  # Will be None for single mode
        )
        db.add(participant)
        db.commit()
        db.refresh(participant)

    # Register users
    for user_id in user_ids:
        registration = TournamentRegistration(
            user_id=user_id,
            tournament_id=player_data.tournament_id,
            registration_date=datetime.now(UTC),
        )
        db.add(registration)
        if participant:
            member = ParticipantMember(participant_id=participant.id, user_id=user_id)
            db.add(member)

    db.commit()

    first_registration = (
        db.query(TournamentRegistration)
        .filter(
            TournamentRegistration.tournament_id == player_data.tournament_id,
            TournamentRegistration.user_id == user_ids[0],
        )
        .first()
    )

    return TournamentRegistrationResponse(
        id=first_registration.id,
        user_id=user_ids[0],
        tournament_id=player_data.tournament_id,
        registration_date=first_registration.registration_date,
    )


@tournaments_router.delete(
    "/registrations/{tournament_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister current user from a tournament",
    description="Removes the current user's registration and associated participant data from a tournament.",
)
def unregister_from_tournament(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    registration = (
        db.query(TournamentRegistration)
        .filter(
            TournamentRegistration.user_id == current_user.id,
            TournamentRegistration.tournament_id == tournament_id,
        )
        .first()
    )
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    participant_members = (
        db.query(ParticipantMember)
        .join(Participant, ParticipantMember.participant_id == Participant.id)
        .filter(
            ParticipantMember.user_id == current_user.id,
            Participant.tournament_id == tournament_id,
        )
        .all()
    )

    for member in participant_members:
        participant = (
            db.query(Participant)
            .filter(Participant.id == member.participant_id)
            .first()
        )
        if participant:
            db.execute(
                delete(ParticipantMember).where(
                    ParticipantMember.participant_id == participant.id
                )
            )
            db.execute(
                delete(MatchPlayer).where(
                    MatchPlayer.match_id.in_(
                        select(Match.id).where(Match.tournament_id == tournament_id)
                    ),
                    MatchPlayer.participant_id == participant.id,
                )
            )
            db.execute(
                delete(pool_participant_association).where(
                    pool_participant_association.c.participant_id == participant.id
                )
            )
            db.delete(participant)

    db.delete(registration)
    db.commit()


@tournaments_router.get(
    "/{tournament_id}/my-registration",
    response_model=bool,
    summary="Check if current user is registered",
    description="Returns true if the current user is registered for the tournament, false otherwise.",
)
def check_my_registration(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    registration = (
        db.query(TournamentRegistration)
        .filter(
            TournamentRegistration.user_id == current_user.id,
            TournamentRegistration.tournament_id == tournament_id,
        )
        .first()
    )
    return registration is not None


@tournaments_router.get(
    "/{tournament_id}/registered-users",
    response_model=List[dict],
    summary="List registered users",
    description="Retrieves all users registered for a tournament with their participant details, if any. Requires admin or editor privileges.",
)
def get_registered_users(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    registrations = (
        db.query(TournamentRegistration)
        .filter(TournamentRegistration.tournament_id == tournament_id)
        .all()
    )
    user_ids = [reg.user_id for reg in registrations]
    users = db.query(User).filter(User.id.in_(user_ids)).all()

    response = []
    for user in users:
        participant_member = (
            db.query(ParticipantMember)
            .join(Participant, ParticipantMember.participant_id == Participant.id)
            .filter(
                ParticipantMember.user_id == user.id,
                Participant.tournament_id == tournament_id,
            )
            .first()
        )
        participant = (
            db.query(Participant)
            .filter(
                Participant.id == participant_member.participant_id,
                Participant.tournament_id == tournament_id,
            )
            .first()
            if participant_member
            else None
        )
        response.append(
            {
                "id": user.id,
                "name": user.name,
                "nickname": user.nickname,
                "participant_id": participant.id if participant else None,
                "participant_name": participant.name if participant else None,
            }
        )
    return response


@tournaments_router.delete(
    "/registrations/user/{user_id}/{tournament_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister a specific user (admin only)",
    description="Removes a specific user's registration and associated participant data from a tournament. Requires admin or editor privileges.",
)
def unregister_user(
    user_id: int,
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    registration = (
        db.query(TournamentRegistration)
        .filter(
            TournamentRegistration.user_id == user_id,
            TournamentRegistration.tournament_id == tournament_id,
        )
        .first()
    )
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    participant_members = (
        db.query(ParticipantMember)
        .join(Participant, ParticipantMember.participant_id == Participant.id)
        .filter(
            ParticipantMember.user_id == user_id,
            Participant.tournament_id == tournament_id,
        )
        .all()
    )

    for member in participant_members:
        participant = (
            db.query(Participant)
            .filter(Participant.id == member.participant_id)
            .first()
        )
        if participant:
            db.execute(
                delete(ParticipantMember).where(
                    ParticipantMember.participant_id == participant.id
                )
            )
            db.execute(
                delete(MatchPlayer).where(
                    MatchPlayer.match_id.in_(
                        select(Match.id).where(Match.tournament_id == tournament_id)
                    ),
                    MatchPlayer.participant_id == participant.id,
                )
            )
            db.execute(
                delete(pool_participant_association).where(
                    pool_participant_association.c.participant_id == participant.id
                )
            )
            db.delete(participant)

    db.delete(registration)
    db.commit()


@tournaments_router.post(
    "/{tournament_id}/participants",
    response_model=ParticipantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a team participant",
    description="Creates a team participant for a tournament in double mode with two registered users and a team name. Requires admin or editor privileges.",
)
def create_participant(
    tournament_id: int,
    participant_data: ParticipantCreate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != "open":
        raise HTTPException(
            status_code=400, detail="Tournament is not open for registration"
        )
    if tournament.mode != "double":
        raise HTTPException(
            status_code=400, detail="Team creation is only allowed in double mode"
        )

    if len(participant_data.user_ids) != 2:
        raise HTTPException(
            status_code=400, detail="Exactly 2 user IDs required for team creation"
        )
    if not participant_data.name:
        raise HTTPException(status_code=400, detail="Team name is required")

    # Verify users exist and are registered
    for user_id in participant_data.user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        registration = (
            db.query(TournamentRegistration)
            .filter(
                TournamentRegistration.user_id == user_id,
                TournamentRegistration.tournament_id == tournament_id,
            )
            .first()
        )
        if not registration:
            raise HTTPException(
                status_code=400,
                detail=f"User {user_id} is not registered for this tournament",
            )

        # Check if user is already in a team
        existing_member = (
            db.query(ParticipantMember)
            .join(Participant, ParticipantMember.participant_id == Participant.id)
            .filter(
                ParticipantMember.user_id == user_id,
                Participant.tournament_id == tournament_id,
            )
            .first()
        )
        if existing_member:
            raise HTTPException(
                status_code=400, detail=f"User {user_id} is already in a team"
            )

    # Create participant
    participant = Participant(tournament_id=tournament_id, name=participant_data.name)
    db.add(participant)
    db.commit()
    db.refresh(participant)

    # Add team members
    for user_id in participant_data.user_ids:
        member = ParticipantMember(participant_id=participant.id, user_id=user_id)
        db.add(member)

    db.commit()

    # Prepare response
    users = [
        PlayerResponse(id=m.user.id, name=m.user.name, nickname=m.user.nickname)
        for m in db.query(ParticipantMember)
        .filter(ParticipantMember.participant_id == participant.id)
        .all()
    ]
    return ParticipantResponse(id=participant.id, name=participant.name, users=users)


@tournaments_router.delete(
    "/{tournament_id}/participants/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a participant",
    description="Deletes a participant (team in double mode or player in single mode) from a tournament, keeping the users' registrations intact if applicable. Requires admin or editor privileges.",
)
def delete_participant(
    tournament_id: int,
    participant_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    # Verify tournament exists and is open
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != "open":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete participants from a tournament that is not open",
        )

    # Verify participant exists
    participant = (
        db.query(Participant)
        .filter(
            Participant.id == participant_id, Participant.tournament_id == tournament_id
        )
        .first()
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # Get member count
    members = (
        db.query(ParticipantMember)
        .filter(ParticipantMember.participant_id == participant_id)
        .all()
    )
    member_count = len(members)

    # Mode-specific validation
    if tournament.mode == "double" and member_count != 2:
        raise HTTPException(
            status_code=400,
            detail="Team participant must have exactly two users to be deleted",
        )
    elif tournament.mode == "single" and member_count > 1:
        raise HTTPException(
            status_code=400,
            detail="Single mode participant cannot have more than one user",
        )

    # Delete associated MatchPlayer entries
    db.execute(
        delete(MatchPlayer).where(
            MatchPlayer.match_id.in_(
                select(Match.id).where(Match.tournament_id == tournament_id)
            ),
            MatchPlayer.participant_id == participant_id,
        )
    )

    # Delete associated pool_participant_association entries
    db.execute(
        delete(pool_participant_association).where(
            pool_participant_association.c.participant_id == participant_id
        )
    )

    # For single mode with 1 member, also delete the associated registration
    if tournament.mode == "single" and member_count == 1:
        user_id = members[0].user_id
        db.execute(
            delete(TournamentRegistration).where(
                TournamentRegistration.user_id == user_id,
                TournamentRegistration.tournament_id == tournament_id,
            )
        )

    # Delete ParticipantMember entries
    db.execute(
        delete(ParticipantMember).where(
            ParticipantMember.participant_id == participant_id
        )
    )

    # Delete the Participant
    db.delete(participant)
    db.commit()


@tournaments_router.get(
    "/{tournament_id}/participants",
    response_model=List[ParticipantResponse],
    summary="List participants of a tournament",
    description="Retrieves all participants (players or teams) for a specific tournament. For single mode, participant names may be null.",
)
def get_participants(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    participants = (
        db.query(Participant).filter(Participant.tournament_id == tournament_id).all()
    )
    response = []
    for p in participants:
        users = [
            PlayerResponse(id=m.user.id, name=m.user.name, nickname=m.user.nickname)
            for m in p.members
        ]
        name = (
            p.name if p.name else (users[0].nickname if users else "")
        )  # Fallback to nickname for single mode
        response.append(ParticipantResponse(id=p.id, name=name, users=users))
    return response


@tournaments_router.post(
    "/{tournament_id}/reset",
    summary="Reset a tournament",
    description="Resets a tournament by deleting all associated matches, pools, and participants, and setting status to 'open'. Requires admin or editor privileges.",
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

    pool_ids = [
        pool.id
        for pool in db.query(Pool).filter(Pool.tournament_id == tournament_id).all()
    ]
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
    description="Retrieves detailed information about a tournament, including pools, participants, and matches.",
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
            name = (
                p.name if p.name else (p.members[0].user.nickname if p.members else "")
            )
            pool_participants.append({"id": p.id, "name": name})
        pool_matches_dict = []
        for m in pool_matches:
            match_participants = []
            for mp in m.match_participations:
                p = mp.participant
                name = (
                    p.name
                    if p.name
                    else (p.members[0].user.nickname if p.members else "")
                )
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
            name = (
                p.name if p.name else (p.members[0].user.nickname if p.members else "")
            )
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


@tournaments_router.patch(
    "/{tournament_id}/registrations/close",
    response_model=TournamentResponse,
    summary="Close registrations for a tournament",
    description="Manually closes registrations by setting status to 'closed'. Requires admin or editor privileges.",
)
def close_tournament_registrations(
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
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament.status != "open":
        raise HTTPException(
            status_code=400, detail="Tournament must be open to close registrations"
        )

    tournament.status = "closed"  # Ferme les inscriptions
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


@tournaments_router.patch(
    "/{tournament_id}/registrations/open",
    response_model=TournamentResponse,
    summary="Close registrations for a tournament",
    description="Manually opens registrations by setting status to 'open'. Requires admin or editor privileges.",
)
def open_tournament_registrations(
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
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament.status != "closed":
        raise HTTPException(
            status_code=400, detail="Tournament must be close to open registrations"
        )

    tournament.status = "open"  # Ouvre les inscriptions
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


@tournaments_router.post(
    "/{tournament_id}/swap-players",
    status_code=status.HTTP_200_OK,
    summary="Swap a wrong participant with the correct user in a finished tournament",
    description="Replaces a wrong participant (single mode) with the correct user in all matches, pools, registrations, etc. Preserves scores and results. Requires admin or editor privileges.",
)
def swap_players(
    tournament_id: int,
    swap_data: SwapPlayersRequest,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != "finished":
        raise HTTPException(
            status_code=400, detail="Only applicable to finished tournaments"
        )
    if tournament.mode != "single":
        raise HTTPException(
            status_code=400, detail="Only supported for single-player mode"
        )

    wrong_participant = (
        db.query(Participant)
        .filter(
            Participant.id == swap_data.wrong_participant_id,
            Participant.tournament_id == tournament_id,
        )
        .first()
    )
    if not wrong_participant:
        raise HTTPException(status_code=404, detail="Wrong participant not found")

    correct_user = db.query(User).filter(User.id == swap_data.correct_user_id).first()
    if not correct_user:
        raise HTTPException(status_code=404, detail="Correct user not found")

    # Ensure correct_user has no existing participant in this tournament
    existing_member = (
        db.query(ParticipantMember)
        .join(Participant, ParticipantMember.participant_id == Participant.id)
        .filter(
            ParticipantMember.user_id == swap_data.correct_user_id,
            Participant.tournament_id == tournament_id,
        )
        .first()
    )
    if existing_member:
        raise HTTPException(
            status_code=400,
            detail="Correct user already has a participant in this tournament",
        )

    # Add registration for correct_user if missing
    existing_reg = (
        db.query(TournamentRegistration)
        .filter(
            TournamentRegistration.user_id == swap_data.correct_user_id,
            TournamentRegistration.tournament_id == tournament_id,
        )
        .first()
    )
    if not existing_reg:
        reg = TournamentRegistration(
            user_id=swap_data.correct_user_id,
            tournament_id=tournament_id,
            registration_date=datetime.now(UTC),
        )
        db.add(reg)

    # Get wrong_user from wrong_participant (assuming single mode: one member)
    wrong_member = (
        db.query(ParticipantMember)
        .filter(ParticipantMember.participant_id == swap_data.wrong_participant_id)
        .first()
    )
    if not wrong_member:
        raise HTTPException(
            status_code=400, detail="No member found for wrong participant"
        )
    wrong_user_id = wrong_member.user_id

    # Create new participant for correct_user
    new_participant = Participant(
        tournament_id=tournament_id,
        name=None,  # Single mode: no team name
    )
    db.add(new_participant)
    db.commit()
    db.refresh(new_participant)

    # Link correct_user to new_participant
    new_member = ParticipantMember(
        participant_id=new_participant.id, user_id=swap_data.correct_user_id
    )
    db.add(new_member)

    # Transfer MatchPlayer entries (preserve scores)
    old_match_players = (
        db.query(MatchPlayer)
        .filter(MatchPlayer.participant_id == swap_data.wrong_participant_id)
        .all()
    )
    for mp in old_match_players:
        new_mp = MatchPlayer(
            match_id=mp.match_id, participant_id=new_participant.id, score=mp.score
        )
        db.add(new_mp)
        db.delete(mp)

    # Transfer pool associations
    db.execute(
        pool_participant_association.update()
        .where(
            pool_participant_association.c.participant_id
            == swap_data.wrong_participant_id
        )
        .values(participant_id=new_participant.id)
    )

    # Clean up old links
    db.delete(wrong_member)
    db.delete(wrong_participant)

    db.execute(
        delete(TournamentRegistration).where(
            TournamentRegistration.user_id == wrong_user_id,
            TournamentRegistration.tournament_id == tournament_id,
        )
    )

    db.commit()

    return {
        "message": "Players swapped successfully. Leaderboards will update on refresh."
    }
