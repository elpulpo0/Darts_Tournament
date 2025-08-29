from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from modules.database.dependencies import get_users_db
from modules.api.tournaments.models import (
    Tournament,
    TournamentRegistration,
    Match,
    MatchPlayer,
    Pool,
    pool_player_association,
)
from modules.api.tournaments.schemas import (
    TournamentCreate,
    TournamentUpdate,
    TournamentResponse,
    TournamentRegistrationCreate,
    TournamentRegistrationResponse,
    MatchCreate,
    MatchUpdate,
    MatchResponse,
    TournamentLeaderboardResponse,
    TournamentLeaderboardEntry,
    SeasonLeaderboardResponse,
    LeaderboardEntry,
    PoolResponse,
    PoolCreate,
    TournamentFullDetailSchema,
    PoolLeaderboardResponse,
)
from modules.api.users.models import User, Role
from modules.api.users.functions import get_current_user
from modules.api.users.schemas import TokenData, PlayerResponse
from typing import List
from datetime import datetime

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
        status=tournament.status,
    )


@tournaments_router.get("/", response_model=List[TournamentResponse])
def get_all_tournaments(db: Session = Depends(get_users_db)):
    tournaments = db.query(Tournament).all()
    return [
        TournamentResponse(
            id=tournament.id,
            name=tournament.name,
            description=tournament.description,
            start_date=tournament.start_date,
            is_active=tournament.is_active,
            type=tournament.type,
            status=tournament.status,
        )
        for tournament in tournaments
    ]


@tournaments_router.get("/{tournament_id}/players", response_model=List[PlayerResponse])
def get_tournament_players(
    tournament_id: int,
    db: Session = Depends(get_users_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    registrations = (
        db.query(TournamentRegistration)
        .filter(TournamentRegistration.tournament_id == tournament_id)
        .all()
    )

    players = [
        PlayerResponse(
            id=registration.user.id,
            name=registration.user.name,
        )
        for registration in registrations
    ]

    return players


@tournaments_router.post(
    "/registrations/",
    response_model=TournamentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user_to_tournament(
    registration_data: TournamentRegistrationCreate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == registration_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    tournament = (
        db.query(Tournament)
        .filter(Tournament.id == registration_data.tournament_id)
        .first()
    )
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != "open":
        raise HTTPException(
            status_code=400, detail="Registrations are closed for this tournament"
        )
    existing_registration = (
        db.query(TournamentRegistration)
        .filter(
            TournamentRegistration.user_id == registration_data.user_id,
            TournamentRegistration.tournament_id == registration_data.tournament_id,
        )
        .first()
    )
    if existing_registration:
        raise HTTPException(
            status_code=400, detail="User already registered to this tournament"
        )
    if current_user.id != registration_data.user_id and not (
        "admin" in current_user.scopes or "editor" in current_user.scopes
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    new_registration = TournamentRegistration(
        user_id=registration_data.user_id,
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

    # Ensure "player" role exists
    player_role = db.query(Role).filter(Role.role == "player").first()
    if not player_role:
        player_role = Role(role="player")
        db.add(player_role)
        db.commit()
        db.refresh(player_role)

    # Check if user with the provided email already exists (if email is provided)
    if player_data.email:
        existing_user = db.query(User).filter(User.email == player_data.email).first()
        if existing_user:
            # If user exists, check if already registered for the tournament
            existing_registration = (
                db.query(TournamentRegistration)
                .filter(
                    TournamentRegistration.user_id == existing_user.id,
                    TournamentRegistration.tournament_id == player_data.tournament_id,
                )
                .first()
            )
            if existing_registration:
                raise HTTPException(
                    status_code=400, detail="User already registered to this tournament"
                )
            user_id = existing_user.id
        else:
            # Create new user
            new_user = User(
                name=player_data.name,
                email=player_data.email,
                hashed_password=None,  # No password for admin-created users
                is_active=True,
                role_id=player_role.id,
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_id = new_user.id
    else:
        # If no email provided, create user with name only
        existing_user = db.query(User).filter(User.name == player_data.name).first()
        if existing_user:
            # If user with same name exists, append a unique identifier
            count = (
                db.query(User).filter(User.name.like(f"{player_data.name}%")).count()
            )
            new_user = User(
                name=f"{player_data.name} {count + 1}",
                email=None,
                hashed_password=None,  # No password for admin-created users
                is_active=True,
                role_id=player_role.id,
            )
        else:
            new_user = User(
                name=player_data.name,
                email=None,
                hashed_password=None,  # No password for admin-created users
                is_active=True,
                role_id=player_role.id,  # Set role_id instead of role
            )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user_id = new_user.id

    # Register the user for the tournament
    new_registration = TournamentRegistration(
        user_id=user_id,
        tournament_id=player_data.tournament_id,
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


@tournaments_router.delete(
    "/registrations/{tournament_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Désinscrire l'utilisateur connecté d'un tournoi non démarré",
)
def unregister_current_user_from_tournament(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    # Sécurité : refuse si pas d'utilisateur authentifié
    if not current_user or not getattr(current_user, "id", None):
        raise HTTPException(status_code=401, detail="Authentication required")

    # Vérifie que le tournoi existe
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != "open":
        raise HTTPException(
            status_code=400,
            detail="Impossible de se désinscrire : le tournoi a déjà commencé.",
        )
    # Cherche l'inscription de l'utilisateur avec le bon id
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
    db.delete(registration)
    db.commit()


@tournaments_router.delete(
    "/registrations/{user_id}/{tournament_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Désinscrire un utilisateur (admin/editor) d'un tournoi non démarré",
)
def unregister_user_from_tournament_admin(
    user_id: int,
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    # Vérifie les droits
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(status_code=403, detail="Admins or editors only")
    # Vérifie existence tournoi et statut
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != "open":
        raise HTTPException(
            status_code=400,
            detail="Impossible de désinscrire : le tournoi a déjà commencé.",
        )
    # Cherche l'inscription de l'utilisateur
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
    db.delete(registration)
    db.commit()


@tournaments_router.get(
    "/registrations/{tournament_id}",
    response_model=List[TournamentRegistrationResponse],
)
def get_tournament_registrations(
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
    return [
        TournamentRegistrationResponse(
            id=registration.id,
            user_id=registration.user_id,
            tournament_id=registration.tournament_id,
            registration_date=registration.registration_date,
        )
        for registration in registrations
    ]


@tournaments_router.get(
    "/{tournament_id}/my-registration",
    response_model=bool,
    summary="Check if the current user is registered for a tournament",
)
def check_user_registration(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    # Verify tournament exists
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Check if the current user is registered
    registration = (
        db.query(TournamentRegistration)
        .filter(
            TournamentRegistration.tournament_id == tournament_id,
            TournamentRegistration.user_id == current_user.id,
        )
        .first()
    )
    return registration is not None


@tournaments_router.post(
    "/matches/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED
)
def create_match(
    match_data: MatchCreate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    if len(match_data.player_ids) != 2:
        raise HTTPException(
            status_code=400, detail="Les matchs doivent avoir exactement 2 joueurs"
        )

    # Ensure tournament exists
    tournament = (
        db.query(Tournament).filter(Tournament.id == match_data.tournament_id).first()
    )
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Ensure tournament is running
    if tournament.status != "running":
        raise HTTPException(
            status_code=400, detail="Tournament must be running to create matches"
        )

    # Ensure all players are registered for the tournament
    for player_id in match_data.player_ids:
        registration = (
            db.query(TournamentRegistration)
            .filter(
                TournamentRegistration.tournament_id == match_data.tournament_id,
                TournamentRegistration.user_id == player_id,
            )
            .first()
        )
        if not registration:
            raise HTTPException(
                status_code=400,
                detail=f"User {player_id} is not registered for this tournament",
            )

    # Ensure player_ids are unique
    unique_player_ids = list(set(match_data.player_ids))
    if len(unique_player_ids) != len(match_data.player_ids):
        raise HTTPException(
            status_code=400, detail="Duplicate player IDs are not allowed in a match"
        )

    # Create the match
    new_match = Match(
        tournament_id=match_data.tournament_id,
        status=match_data.status,
        pool_id=match_data.pool_id,
        round=match_data.round or 1,
    )
    db.add(new_match)
    db.commit()
    db.refresh(new_match)

    # Add players to the match, checking for existing MatchPlayer records
    for player_id in unique_player_ids:
        # Check if the player is already associated with this match
        existing_match_player = (
            db.query(MatchPlayer)
            .filter(
                MatchPlayer.match_id == new_match.id,
                MatchPlayer.user_id == player_id,
            )
            .first()
        )
        if existing_match_player:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Player {player_id} is already associated with this match",
            )

        match_player = MatchPlayer(match_id=new_match.id, user_id=player_id, score=None)
        db.add(match_player)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to create match due to a database integrity error",
        )

    db.refresh(new_match)
    players = [
        {"user_id": mp.user_id, "name": mp.user.name, "score": mp.score}
        for mp in new_match.match_players
    ]
    return MatchResponse(
        id=new_match.id,
        tournament_id=new_match.tournament_id,
        status=new_match.status,
        players=players,
        pool_id=new_match.pool_id,
        round=new_match.round,
    )


@tournaments_router.get("/matches/{match_id}", response_model=MatchResponse)
def get_match(
    match_id: int,
    db: Session = Depends(get_users_db),
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    players = [
        {"user_id": mp.user_id, "name": mp.user.name, "score": mp.score}
        for mp in match.match_players
    ]
    return MatchResponse(
        id=match.id,
        tournament_id=match.tournament_id,
        status=match.status,
        players=players,
        pool_id=match.pool_id,
        round=match.round,
    )


@tournaments_router.get(
    "/matches/tournament/{tournament_id}", response_model=List[MatchResponse]
)
def get_matches_by_tournament(
    tournament_id: int,
    db: Session = Depends(get_users_db),
):
    matches = db.query(Match).filter(Match.tournament_id == tournament_id).all()
    if not matches:
        return []
    return [
        MatchResponse(
            id=match.id,
            tournament_id=match.tournament_id,
            status=match.status,
            players=[
                {"user_id": mp.user_id, "name": mp.user.name, "score": mp.score}
                for mp in match.match_players
            ],
            pool_id=match.pool_id,
            round=match.round,
        )
        for match in matches
    ]


@tournaments_router.patch("/matches/{match_id}", response_model=MatchResponse)
def update_match(
    match_id: int,
    update_data: MatchUpdate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if update_data.status:
        match.status = update_data.status
    if update_data.scores:
        # Vérifier qu'il n'y a pas de match nul si le statut est "completed"
        if update_data.status == "completed":
            scores = [score_data["score"] for score_data in update_data.scores]
            if len(scores) == 2 and scores[0] == scores[1]:
                raise HTTPException(
                    status_code=400,
                    detail="Matchs nuls non autorisés",
                )
        for score_data in update_data.scores:
            match_player = (
                db.query(MatchPlayer)
                .filter(
                    MatchPlayer.match_id == match_id,
                    MatchPlayer.user_id == score_data["user_id"],
                )
                .first()
            )
            if not match_player:
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {score_data['user_id']} not found in match",
                )
            match_player.score = score_data[
                "score"
            ]  # Stocker le score brut (manches gagnées)
    db.commit()
    db.refresh(match)
    players = [
        {"user_id": mp.user_id, "name": mp.user.name, "score": mp.score}
        for mp in match.match_players
    ]
    return MatchResponse(
        id=match.id,
        tournament_id=match.tournament_id,
        status=match.status,
        players=players,
        pool_id=match.pool_id,
    )


@tournaments_router.get(
    "/leaderboard/tournament/{tournament_id}",
    response_model=TournamentLeaderboardResponse,
)
def get_tournament_leaderboard(
    tournament_id: int,
    db: Session = Depends(get_users_db),
):
    # Vérifier si le tournoi existe
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Récupérer tous les matchs complétés du tournoi
    matches = (
        db.query(Match)
        .filter(Match.tournament_id == tournament_id, Match.status == "completed")
        .all()
    )

    # Calculer stats par joueur
    stats = {}
    for match in matches:
        if len(match.match_players) != 2:
            continue  # Ignorer les matchs non binaires
        p1, p2 = match.match_players
        if p1.score is None or p2.score is None:
            continue
        # Initialiser stats si nécessaire
        if p1.user_id not in stats:
            stats[p1.user_id] = {"name": p1.user.name, "wins": 0, "total_manches": 0}
        if p2.user_id not in stats:
            stats[p2.user_id] = {"name": p2.user.name, "wins": 0, "total_manches": 0}
        # Ajouter manches gagnées
        stats[p1.user_id]["total_manches"] += p1.score
        stats[p2.user_id]["total_manches"] += p2.score
        # Compter victoire (pas de bonus de points)
        if p1.score > p2.score:
            stats[p1.user_id]["wins"] += 1
        elif p2.score > p1.score:
            stats[p2.user_id]["wins"] += 1

    # Créer les entrées et trier (wins desc, puis total_manches desc)
    leaderboard_entries = [
        TournamentLeaderboardEntry(
            user_id=user_id,
            name=data["name"],
            wins=data["wins"],
            total_manches=data["total_manches"],
        )
        for user_id, data in stats.items()
    ]
    leaderboard_entries.sort(key=lambda e: (-e.wins, -e.total_manches))

    return TournamentLeaderboardResponse(
        tournament_id=tournament_id,
        leaderboard=leaderboard_entries,
    )


@tournaments_router.get(
    "/leaderboard/season/{year}", response_model=SeasonLeaderboardResponse
)
def get_season_leaderboard(
    year: int,
    db: Session = Depends(get_users_db),
):
    # Calcul de la saison
    season_start_year = year if datetime.now().month >= 9 else year - 1
    season_end_year = season_start_year + 1

    # Include tournaments from both season start year and provided year
    matches = (
        db.query(Match)
        .join(Tournament, Match.tournament_id == Tournament.id)
        .filter(
            func.extract("year", Tournament.start_date).in_([season_start_year, year])
        )
        .filter(Match.status == "completed")
        .all()
    )

    # Debug logging
    print(
        f"Fetching matches for season {season_start_year}-{season_end_year} and year {year}"
    )
    print(f"Found {len(matches)} completed matches")

    stats = {}
    for match in matches:
        if len(match.match_players) != 2:
            continue
        p1, p2 = match.match_players
        if p1.score is None or p2.score is None:
            continue
        if p1.user_id not in stats:
            stats[p1.user_id] = {
                "name": p1.user.name,
                "total_points": 0,
                "wins": 0,
                "total_manches": 0,
            }
        if p2.user_id not in stats:
            stats[p2.user_id] = {
                "name": p2.user.name,
                "total_points": 0,
                "wins": 0,
                "total_manches": 0,
            }
        # Add manches (scores)
        stats[p1.user_id]["total_manches"] += p1.score
        stats[p2.user_id]["total_manches"] += p2.score
        # Add win bonus to total_points (as before)
        if p1.score > p2.score:
            stats[p1.user_id]["wins"] += 1
            stats[p1.user_id]["total_points"] += p1.score + 1  # Score + win bonus
            stats[p2.user_id]["total_points"] += p2.score
        elif p2.score > p1.score:
            stats[p2.user_id]["wins"] += 1
            stats[p2.user_id]["total_points"] += p2.score + 1  # Score + win bonus
            stats[p1.user_id]["total_points"] += p1.score

    leaderboard_entries = [
        LeaderboardEntry(
            user_id=user_id,
            name=data["name"],
            total_points=data["total_points"],
            wins=data["wins"],
            total_manches=data["total_manches"],
        )
        for user_id, data in stats.items()
    ]
    leaderboard_entries.sort(key=lambda e: (-e.total_points, -e.wins, -e.total_manches))

    return SeasonLeaderboardResponse(
        season=f"{season_start_year}-{season_end_year}",
        leaderboard=leaderboard_entries,
    )


@tournaments_router.get(
    "/{tournament_id}/pools/leaderboard",
    response_model=List[PoolLeaderboardResponse],
)
def get_pools_leaderboard(
    tournament_id: int,
    db: Session = Depends(get_users_db),
):
    # Vérifier si le tournoi existe
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Récupérer toutes les poules du tournoi
    pools = db.query(Pool).filter(Pool.tournament_id == tournament_id).all()
    if not pools:
        return []

    # Calculer le classement pour chaque poule
    leaderboards = []
    for pool in pools:
        # Récupérer tous les matchs complétés de la poule
        matches = (
            db.query(Match)
            .filter(Match.pool_id == pool.id, Match.status == "completed")
            .all()
        )

        # Calculer stats par joueur pour cette poule
        stats = {}
        for match in matches:
            if len(match.match_players) != 2:
                continue  # Ignorer les matchs non binaires
            p1, p2 = match.match_players
            if p1.score is None or p2.score is None:
                continue
            # Initialiser stats si nécessaire
            if p1.user_id not in stats:
                stats[p1.user_id] = {
                    "name": p1.user.name,
                    "wins": 0,
                    "total_manches": 0,
                }
            if p2.user_id not in stats:
                stats[p2.user_id] = {
                    "name": p2.user.name,
                    "wins": 0,
                    "total_manches": 0,
                }
            # Ajouter manches gagnées
            stats[p1.user_id]["total_manches"] += p1.score
            stats[p2.user_id]["total_manches"] += p2.score
            # Compter victoire (pas de bonus de points)
            if p1.score > p2.score:
                stats[p1.user_id]["wins"] += 1
            elif p2.score > p1.score:
                stats[p2.user_id]["wins"] += 1

        # Créer les entrées et trier (wins desc, puis total_manches desc)
        leaderboard_entries = [
            TournamentLeaderboardEntry(
                user_id=user_id,
                name=data["name"],
                wins=data["wins"],
                total_manches=data["total_manches"],
            )
            for user_id, data in stats.items()
        ]
        leaderboard_entries.sort(key=lambda e: (-e.wins, -e.total_manches))

        leaderboards.append(
            PoolLeaderboardResponse(
                tournament_id=tournament_id,
                pool_id=pool.id,
                pool_name=pool.name or f"Poule {pool.id}",
                leaderboard=leaderboard_entries,
            )
        )

    return leaderboards


@tournaments_router.post("/{tournament_id}/pools/", response_model=PoolResponse)
def create_pool(
    tournament_id: int,
    pool_data: PoolCreate,
    db: Session = Depends(get_users_db),
):
    try:
        # Unicité des joueurs pour la pool (empêche doublon-clé)
        unique_player_ids = list(set(pool_data.player_ids))

        # Crée pool
        new_pool = Pool(tournament_id=tournament_id, name=pool_data.name)
        db.add(new_pool)
        db.commit()
        db.refresh(new_pool)

        # Associe uniquement les joueurs non déjà présents ! (déjà assuré par set mais on vérifie)
        for pid in unique_player_ids:
            user = db.query(User).get(pid)
            if user and user not in new_pool.players:
                new_pool.players.append(user)

        db.commit()

        # Retour direct en s'appuyant sur Pydantic (nécessite model_config/from_attributes sur PoolResponse)
        return PoolResponse.model_validate(new_pool)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Erreur d'intégrité : joueur déjà dans cette pool ou autre problème BDD.",
        )


@tournaments_router.get(
    "/{tournament_id}/pools",
    response_model=List[PoolResponse],
    summary="Get all pools for a tournament",
)
def get_tournament_pools(tournament_id: int, db: Session = Depends(get_users_db)):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    pools = db.query(Pool).filter(Pool.tournament_id == tournament_id).all()
    return [
        PoolResponse(
            id=pool.id,
            players=[PlayerResponse(id=p.id, name=p.name) for p in pool.players],
            matches=[
                MatchResponse(
                    id=m.id,
                    tournament_id=m.tournament_id,
                    status=m.status,
                    players=[
                        {"user_id": mp.user_id, "name": mp.user.name, "score": mp.score}
                        for mp in m.match_players
                    ],
                    pool_id=m.pool_id,
                    round=m.round,
                )
                for m in pool.matches
            ],
        )
        for pool in pools
    ]


@tournaments_router.post(
    "/{tournament_id}/reset",
    summary="Réinitialise complètement un tournoi (supprime matches, pools et remet le statut open)",
)
def reset_tournament(tournament_id: int, db: Session = Depends(get_users_db)):
    try:
        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")

        # Supprimer explicitement les enregistrements de match_players
        db.query(MatchPlayer).filter(
            MatchPlayer.match_id.in_(
                db.query(Match.id).filter(Match.tournament_id == tournament_id)
            )
        ).delete(synchronize_session=False)

        # Supprimer tous les matchs du tournoi
        db.query(Match).filter(Match.tournament_id == tournament_id).delete(
            synchronize_session=False
        )

        # Supprimer les associations joueur-poule
        pool_ids = [
            p.id
            for p in db.query(Pool.id).filter(Pool.tournament_id == tournament_id).all()
        ]
        if pool_ids:
            db.execute(
                delete(pool_player_association).where(
                    pool_player_association.c.pool_id.in_(pool_ids)
                )
            )

        # Supprimer toutes les poules du tournoi
        db.query(Pool).filter(Pool.tournament_id == tournament_id).delete(
            synchronize_session=False
        )

        # Réinitialiser le statut et le type du tournoi
        tournament.status = "open"
        tournament.type = None
        db.commit()

        return {"reset": True}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la réinitialisation: {str(e)}"
        )


@tournaments_router.get(
    "/{tournament_id}/details", response_model=TournamentFullDetailSchema
)
def get_full_tournament_details(
    tournament_id: int, db: Session = Depends(get_users_db)
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found.")
    # pools avec joueurs :
    pools = db.query(Pool).filter(Pool.tournament_id == tournament_id).all()
    # On regroupe les matches par pool
    pool_dicts = []
    for pool in pools:
        pool_matches = db.query(Match).filter(Match.pool_id == pool.id).all()
        pool_players = [{"id": p.id, "name": p.name} for p in pool.players]
        pool_matches_dict = []
        for m in pool_matches:
            pool_matches_dict.append(
                {
                    "id": m.id,
                    "players": [
                        {
                            "id": mp.user_id,
                            "name": mp.user.name if mp.user else "",
                            "score": mp.score,
                        }
                        for mp in m.match_players
                    ],
                    "status": m.status,
                    "round": m.round,
                }
            )
        pool_dicts.append(
            {
                "id": pool.id,
                "name": pool.name,
                "players": pool_players,
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
        finals_matches_dict.append(
            {
                "id": m.id,
                "players": [
                    {
                        "id": mp.user_id,
                        "name": mp.user.name if mp.user else "",
                        "score": mp.score,
                    }
                    for mp in m.match_players
                ],
                "status": m.status,
                "round": m.round,
            }
        )

    return {
        "id": tournament.id,
        "name": tournament.name,
        "type": tournament.type,
        "status": tournament.status,
        "pools": pool_dicts,
        "final_matches": finals_matches_dict,
    }
