from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    nickname = Column(String(255), nullable=True)
    usual_number = Column(String(10), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class JerseyWash(Base):
    __tablename__ = "jersey_washes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    taken_at = Column(DateTime, server_default=func.now())
