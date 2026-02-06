from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Player
from app.schemas import PlayerResponse

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("", response_model=list[PlayerResponse])
def get_players(db: Session = Depends(get_db)):
    return db.query(Player).all()
