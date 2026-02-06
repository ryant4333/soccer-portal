from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Player
from app.schemas import PlayerCreate, PlayerResponse, PlayerUpdate

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


@router.put("/{player_id}", response_model=PlayerResponse)
def update_player(player_id: int, player: PlayerUpdate, db: Session = Depends(get_db)):
    db_player = db.query(Player).filter(Player.id == player_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
    if player.name is not None:
        db_player.name = player.name
    if player.nickname is not None:
        db_player.nickname = player.nickname
    if player.usual_number is not None:
        db_player.usual_number = player.usual_number
    db.commit()
    db.refresh(db_player)
    return db_player


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(player_id: int, db: Session = Depends(get_db)):
    db_player = db.query(Player).filter(Player.id == player_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
    db.delete(db_player)
    db.commit()
