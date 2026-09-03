"""Tests for Phase 2: database persistence."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pytest
from sqlalchemy.orm import Session

from app.db.database import engine, SessionLocal, Base, init_db
from app.db import persistence
from app.game.state import create_game_state
from app.game import event_log


@pytest.fixture(autouse=True)
def setup_db():
    """Use in-memory SQLite for tests."""
    from app.db import database
    # Recreate tables for each test
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_save_and_load_game():
    """A game can be saved and loaded from the database."""
    state = create_game_state("test_db", seed=42)
    event_log.log_night_begin(state, 1)

    db = SessionLocal()
    try:
        persistence.save_game(db, state)
        loaded = persistence.load_game(db, "test_db")
        assert loaded is not None
        assert loaded.id == "test_db"
        assert len(loaded.players) == 5
        assert loaded.phase == state.phase
        assert len(loaded.events) == len(state.events)
    finally:
        db.close()


def test_events_persist():
    """Events are saved and retrieved correctly."""
    state = create_game_state("test_events", seed=10)
    event_log.log_night_begin(state, 1)
    event_log.log_mafia_kill(state, 1, "Alice")
    event_log.log_day_begin(state, 1)

    db = SessionLocal()
    try:
        persistence.save_game(db, state)
        events = persistence.get_events(db, "test_events")
        assert len(events) == 3
        assert events[0]["event_type"] == "night_begin"
        assert events[1]["event_type"] == "mafia_kill"
        assert events[2]["event_type"] == "day_begin"
    finally:
        db.close()


def test_player_state_persists():
    """Player alive status and role persist correctly."""
    state = create_game_state("test_players", seed=5)
    # Kill one player
    state.players[0].alive = False

    db = SessionLocal()
    try:
        persistence.save_game(db, state)
        loaded = persistence.load_game(db, "test_players")
        assert loaded is not None
        assert loaded.players[0].alive == False
        assert loaded.players[1].alive == True
    finally:
        db.close()
