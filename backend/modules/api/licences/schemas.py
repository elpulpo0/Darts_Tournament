from pydantic import BaseModel, ConfigDict
from typing import Optional


class LicenceCreate(BaseModel):
    ligue: str
    comite: str
    club_number: int
    club_name: str
    name: str
    surname: str
    category: str
    licence_number: int
    user_id: int


class LicenceResponse(BaseModel):
    id: int
    ligue: str
    comite: str
    club_number: int
    club_name: str
    name: str
    surname: str
    category: str
    licence_number: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class LicenceUpdate(BaseModel):
    ligue: Optional[str] = None
    comite: Optional[str] = None
    club_number: Optional[int] = None
    club_name: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    category: Optional[str] = None
    licence_number: Optional[int] = None
    user_id: Optional[int] = None
