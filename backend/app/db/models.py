"""SQLAlchemy models for game persistence."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GameModel(Base):
    """A single Among Agents game instance."""
    __tablename__ = "games"

    id = Column(String, primary_key=True)
    phase = Column(String, default="waiting")
    round_number = Column(Integer, default=0)
    winner = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    players = relationship("PlayerModel", back_populates="game", cascade="all, delete-orphan")
    events = relationship("EventModel", back_populates="game", cascade="all, delete-orphan")


class PlayerModel(Base):
    """A player in a game."""
    __tablename__ = "players"

    id = Column(String, primary_key=True)
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    name = Column(String, nullable=False)
    personality = Column(String, nullable=False)
    role = Column(String, nullable=False)
    alive = Column(Boolean, default=True)
    # JSON-serialized private state
    suspicions_json = Column(Text, default="{}")
    memories_json = Column(Text, default="[]")
    investigation_results_json = Column(Text, default="{}")

    game = relationship("GameModel", back_populates="players")

    @property
    def suspicions(self) -> dict:
        return json.loads(self.suspicions_json) if self.suspicions_json else {}

    @suspicions.setter
    def suspicions(self, value: dict):
        self.suspicions_json = json.dumps(value)

    @property
    def memories(self) -> list:
        return json.loads(self.memories_json) if self.memories_json else []

    @memories.setter
    def memories(self, value: list):
        self.memories_json = json.dumps(value)

    @property
    def investigation_results(self) -> dict:
        return json.loads(self.investigation_results_json) if self.investigation_results_json else {}

    @investigation_results.setter
    def investigation_results(self, value: dict):
        self.investigation_results_json = json.dumps(value)


class EventModel(Base):
    """A logged event in a game's timeline."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    phase = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    public = Column(Boolean, default=True)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=_utcnow)

    game = relationship("GameModel", back_populates="events")

    @property
    def meta(self) -> dict:
        return json.loads(self.metadata_json) if self.metadata_json else {}

    @meta.setter
    def meta(self, value: dict):
        self.metadata_json = json.dumps(value)
