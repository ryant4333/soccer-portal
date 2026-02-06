from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PlayerCreate(BaseModel):
    name: str
    nickname: Optional[str] = None
    usual_number: Optional[str] = None


class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    usual_number: Optional[str] = None


class PlayerResponse(BaseModel):
    id: int
    name: str
    nickname: Optional[str]
    usual_number: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class JerseyWashCreate(BaseModel):
    player_id: int


class JerseyWashResponse(BaseModel):
    id: int
    player_id: int
    taken_at: datetime

    model_config = {"from_attributes": True}


class CurrentHolder(BaseModel):
    player: PlayerResponse
    taken_at: datetime


class JerseyRosterEntry(BaseModel):
    player: PlayerResponse
    wash_count: int
