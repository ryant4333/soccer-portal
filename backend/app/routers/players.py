from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Player
from app.schemas import PlayerCreate, PlayerResponse

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("", response_model=list[PlayerResponse])
def get_players(db: Session = Depends(get_db)):
    return db.query(Player).all()


@router.post("", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player(player: PlayerCreate, db: Session = Depends(get_db)):
    db_player = Player(
        name=player.name,
        nickname=player.nickname,
        usual_number=player.usual_number,
    )
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player
