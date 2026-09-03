"""Game API routes: REST endpoints for creating and controlling games."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import persistence
from app.agents.manager import AgentManager
from app.game.engine import GameEngine

router = APIRouter(prefix="/games", tags=["games"])

# In-memory store of active game engines (keyed by game_id)
# The DB stores state; the engine holds the live agent manager
_engines: dict[str, GameEngine] = {}


def _get_or_rebuild_engine(game_id: str, db: Session) -> GameEngine:
    """Get the in-memory engine, or rebuild it from the database."""
    if game_id in _engines:
        return _engines[game_id]

    state = persistence.load_game(db, game_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found.")

    manager = AgentManager()
    engine = GameEngine(manager)
    engine.state = state
    manager.initialize(state)
    _engines[game_id] = engine
    return engine


@router.post("")
def create_game(db: Session = Depends(get_db)):
    """Create a new game."""
    game_id = str(uuid.uuid4())[:8]

    manager = AgentManager()
    engine = GameEngine(manager)
    state = engine.create_game(game_id)

    _engines[game_id] = engine
    persistence.save_game(db, state)

    return {"game_id": game_id, "state": state.to_public_dict()}


@router.get("/{game_id}")
def get_game(game_id: str, debug: bool = False, db: Session = Depends(get_db)):
    """Get the public game state. Use ?debug=true for full private state."""
    engine = _get_or_rebuild_engine(game_id, db)
    state = engine.get_state()

    if debug:
        return state.to_debug_dict()
    return state.to_public_dict()


@router.post("/{game_id}/next")
def advance_game(game_id: str, db: Session = Depends(get_db)):
    """Advance the game by one meaningful event."""
    engine = _get_or_rebuild_engine(game_id, db)

    if engine.state.winner is not None:
        return {
            "phase": "game_over",
            "round_number": engine.state.round_number,
            "events": [],
            "winner": engine.state.winner,
            "game_over": True,
            "alive_count": len(engine.state.living_players()),
        }

    result = engine.step()
    persistence.save_game(db, engine.state)

    return result


@router.post("/{game_id}/autoplay")
def set_autoplay(game_id: str, enabled: bool = True, db: Session = Depends(get_db)):
    """Enable or disable autoplay for a game. (Frontend manages the loop.)"""
    engine = _get_or_rebuild_engine(game_id, db)
    return {"game_id": game_id, "autoplay": enabled}


@router.post("/{game_id}/reset")
def reset_game(game_id: str, db: Session = Depends(get_db)):
    """Reset the game with a new state."""
    engine = _get_or_rebuild_engine(game_id, db)
    state = engine.reset()
    persistence.save_game(db, state)

    return {"game_id": game_id, "state": state.to_public_dict()}


@router.get("/{game_id}/events")
def get_events(game_id: str, debug: bool = False, db: Session = Depends(get_db)):
    """Get chronological events for a game."""
    events = persistence.get_events(db, game_id, public_only=not debug)
    return {"game_id": game_id, "events": events}
