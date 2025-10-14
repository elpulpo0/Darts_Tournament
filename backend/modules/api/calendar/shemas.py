from pydantic import BaseModel, ConfigDict
from typing import Optional


class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    organiser: Optional[str] = None
    place: Optional[str] = None
    date: str


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    organiser: Optional[str] = None
    place: Optional[str] = None
    date: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    organiser: Optional[str]
    place: Optional[str]
    date: str

    model_config = ConfigDict(from_attributes=True)
