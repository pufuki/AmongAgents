"""Game persistence: save and load GameState from the database."""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import GameModel, PlayerModel, EventModel
from app.game.state import GameState, Player, GameEvent


def save_game(db: Session, state: GameState) -> None:
    """Persist a full GameState (players + events) to the database."""
    game = db.get(GameModel, state.id)
    if game is None:
        game = GameModel(id=state.id)
        db.add(game)

    game.phase = state.phase
    game.round_number = state.round_number
    game.winner = state.winner

    # Clear and re-add players (simpler than diffing)
    db.query(PlayerModel).filter(PlayerModel.game_id == state.id).delete()
    for p in state.players:
        pm = PlayerModel(
            id=f"{state.id}_{p.id}",
            game_id=state.id,
            name=p.name,
            personality=p.personality,
            role=p.role,
            alive=p.alive,
        )
        pm.suspicions = dict(p.suspicions)
        pm.memories = list(p.memories)
        pm.investigation_results = dict(p.investigation_results)
        db.add(pm)

    # Clear and re-add events
    db.query(EventModel).filter(EventModel.game_id == state.id).delete()
    for e in state.events:
        em = EventModel(
            game_id=state.id,
            round_number=e.round_number,
            phase=e.phase,
            event_type=e.event_type,
            message=e.message,
            public=e.public,
        )
        em.meta = dict(e.metadata)
        db.add(em)

    db.commit()


def load_game(db: Session, game_id: str) -> Optional[GameState]:
    """Load a GameState from the database. Returns None if not found."""
    game = db.get(GameModel, game_id)
    if game is None:
        return None

    player_models = (
        db.query(PlayerModel)
        .filter(PlayerModel.game_id == game_id)
        .order_by(PlayerModel.name)
        .all()
    )

    players = []
    for pm in player_models:
        # Extract original player_id from the composite key
        original_id = pm.id.replace(f"{game_id}_", "", 1)
        player = Player(
            id=original_id,
            name=pm.name,
            personality=pm.personality,
            role=pm.role,
            alive=pm.alive,
            investigation_results=dict(pm.investigation_results),
            suspicions=dict(pm.suspicions),
            memories=list(pm.memories),
        )
        players.append(player)

    event_models = (
        db.query(EventModel)
        .filter(EventModel.game_id == game_id)
        .order_by(EventModel.id)
        .all()
    )

    events = []
    max_event_id = 0
    for em in event_models:
        events.append(GameEvent(
            id=em.id,
            round_number=em.round_number,
            phase=em.phase,
            event_type=em.event_type,
            message=em.message,
            public=em.public,
            metadata=dict(em.meta),
        ))
        max_event_id = max(max_event_id, em.id)

    state = GameState(
        id=game_id,
        players=players,
        phase=game.phase,
        round_number=game.round_number,
        events=events,
        winner=game.winner,
    )
    state._event_counter = max_event_id
    return state


def get_events(db: Session, game_id: str, public_only: bool = True) -> list[dict]:
    """Get events for a game as dicts."""
    query = db.query(EventModel).filter(EventModel.game_id == game_id)
    if public_only:
        query = query.filter(EventModel.public == True)
    events = query.order_by(EventModel.id).all()
    return [
        {
            "id": e.id,
            "round_number": e.round_number,
            "phase": e.phase,
            "event_type": e.event_type,
            "message": e.message,
            "public": e.public,
            "metadata": e.meta,
        }
        for e in events
    ]
