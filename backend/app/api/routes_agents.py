"""Agent API routes: inspect agent state."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import persistence

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/{game_id}/{player_id}")
def get_agent_state(game_id: str, player_id: str, debug: bool = False,
                    db: Session = Depends(get_db)):
    """Get the state of a specific agent in a game.

    Without debug mode, returns only public information.
    With debug=true, returns private state (role, suspicions, memories).
    """
    state = persistence.load_game(db, game_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found.")

    player = state.get_player(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found.")

    if debug:
        return player.to_private_dict()
    return player.to_public_dict()


@router.get("/{game_id}")
def get_all_agents(game_id: str, debug: bool = False, db: Session = Depends(get_db)):
    """Get all agents' states for a game."""
    state = persistence.load_game(db, game_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found.")

    if debug:
        return [p.to_private_dict() for p in state.players]
    return [p.to_public_dict() for p in state.players]
