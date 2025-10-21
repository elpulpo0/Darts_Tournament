from pydantic import BaseModel, ConfigDict
from typing import Optional


class InscriptionCreate(BaseModel):
    date: str
    name: str
    surname: str
    club: str
    player_number: Optional[int] = None
    category_simple: Optional[str] = None
    category_double: Optional[str] = None
    doublette: Optional[int] = None


class InscriptionResponse(BaseModel):
    id: int
    date: str
    name: str
    surname: str
    club: str
    player_number: Optional[int] = None
    category_simple: Optional[str] = None
    category_double: Optional[str] = None
    doublette: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class InscriptionUpdate(BaseModel):
    date: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    club: Optional[str] = None
    player_number: Optional[int] = None
    category_simple: Optional[str] = None
    category_double: Optional[str] = None
    doublette: Optional[int] = None
