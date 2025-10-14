from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from modules.database.dependencies import get_users_db
from modules.api.calendar.models import Event
from modules.api.calendar.shemas import (
    EventCreate,
    EventUpdate,
    EventResponse,
)
from modules.api.users.functions import get_current_user
from modules.api.users.schemas import TokenData
from typing import List

calendar_router = APIRouter(prefix="/events", tags=["Calendar"])


@calendar_router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event",
    description="Creates a new event with the provided details. Requires admin or editor privileges.",
)
def create_Event(
    event_data: EventCreate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )
    new_event = Event(
        name=event_data.name,
        description=event_data.description,
        organiser=event_data.organiser,
        place=event_data.place,
        date=event_data.date,
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return EventResponse(
        id=new_event.id,
        name=new_event.name,
        description=new_event.description,
        organiser=new_event.organiser,
        place=new_event.place,
        date=new_event.date,
    )


@calendar_router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an event",
    description="Deletes an event. Requires admin or editor privileges.",
)
def delete_event(
    event_id: int,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    db.delete(event)
    db.commit()


@calendar_router.patch(
    "/{event_id}",
    response_model=EventResponse,
    summary="Update an event",
    description="Updates an event's details. Requires admin or editor privileges.",
)
def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_users_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not ("admin" in current_user.scopes or "editor" in current_user.scopes):
        raise HTTPException(
            status_code=403, detail="Access denied: administrators or editors only."
        )

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Update Event fields
    for field, value in event_data.dict(exclude_unset=True).items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return EventResponse(
        id=event.id,
        name=event.name,
        organiser=event.organiser,
        description=event.description,
        place=event.place,
        date=event.date,
    )


@calendar_router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get an event by ID",
    description="Retrieves details of a specific event by its ID.",
)
def get_event(
    event_id: int,
    db: Session = Depends(get_users_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventResponse(
        id=event.id,
        name=event.name,
        organiser=event.organiser,
        description=event.description,
        place=event.place,
        date=event.date,
    )


@calendar_router.get(
    "/",
    response_model=List[EventResponse],
    summary="List all events",
    description="Retrieves a list of all events in the system.",
)
def get_events(
    db: Session = Depends(get_users_db),
):
    events = db.query(Event).all()
    return [
        EventResponse(
            id=event.id,
            name=event.name,
            organiser=event.organiser,
            description=event.description,
            place=event.place,
            date=event.date,
        )
        for event in events
    ]
