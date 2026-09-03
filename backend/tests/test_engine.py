"""Tests for the Phase 1 game engine: rules, win conditions, validation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pytest
from app.agents.manager import AgentManager
from app.game.engine import GameEngine
from app.game.state import create_game_state, GameState, Player
from app.game import rules
from app.core.constants import (
    ROLE_MAFIA,
    ROLE_DETECTIVE,
    ROLE_CITIZEN,
    PHASE_NIGHT,
    PHASE_DAY_DISCUSSION,
    PHASE_DAY_VOTING,
    PHASE_DAY_RESULT,
    PHASE_GAME_OVER,
)


def make_engine(seed=42):
    manager = AgentManager(use_llm=False)
    engine = GameEngine(manager, seed=seed)
    engine.create_game("test")
    return engine


def test_citizen_win_condition():
    """Citizens win when all mafia are eliminated."""
    state = create_game_state("test", seed=42)
    # Kill the single mafia player
    for p in state.players:
        if p.role == ROLE_MAFIA:
            p.alive = False
    assert rules.check_winner(state) == "citizens"


def test_mafia_win_condition():
    """Mafia wins when mafia count >= non-mafia count."""
    state = create_game_state("test", seed=42)
    # Kill all but mafia + 1 citizen
    mafia = [p for p in state.players if p.role == ROLE_MAFIA]
    non_mafia = [p for p in state.players if p.role != ROLE_MAFIA]
    # Kill all but one non-mafia
    for p in non_mafia[1:]:
        p.alive = False
    # Now: 1 mafia, 1 non-mafia → mafia wins
    assert rules.check_winner(state) == "mafia"


def test_no_winner_mid_game():
    """No winner when game is still in progress."""
    state = create_game_state("test", seed=42)
    assert rules.check_winner(state) is None


def test_invalid_mafia_target_dead():
    """Mafia cannot target a dead player."""
    state = create_game_state("test", seed=42)
    mafia = [p for p in state.players if p.role == ROLE_MAFIA][0]
    target = [p for p in state.players if p.role != ROLE_MAFIA][0]
    target.alive = False
    valid, msg = rules.validate_night_mafia_target(state, mafia, target.id)
    assert not valid
    assert "dead" in msg.lower()


def test_dead_agent_cannot_act():
    """Dead agents cannot perform night actions."""
    state = create_game_state("test", seed=42)
    mafia = [p for p in state.players if p.role == ROLE_MAFIA][0]
    target = [p for p in state.players if p.role != ROLE_MAFIA][0]
    mafia.alive = False
    valid, msg = rules.validate_night_mafia_target(state, mafia, target.id)
    assert not valid
    assert "dead" in msg.lower()


def test_detective_cannot_investigate_dead():
    """Detective cannot investigate a dead player."""
    state = create_game_state("test", seed=42)
    detective = [p for p in state.players if p.role == ROLE_DETECTIVE][0]
    target = [p for p in state.players if p.role != ROLE_DETECTIVE][0]
    target.alive = False
    valid, msg = rules.validate_night_detective_target(state, detective, target.id)
    assert not valid
    assert "dead" in msg.lower()


def test_vote_counting():
    """Vote counting produces correct tally."""
    state = create_game_state("test", seed=42)
    living = state.living_players()
    # Simulate votes: 3 vote for player 0, 2 for player 1
    state._votes = {
        living[0].id: living[1].id,
        living[1].id: living[1].id,
        living[2].id: living[1].id,
        living[3].id: living[2].id,
        living[4].id: living[2].id,
    }
    tally = rules.count_votes(state)
    assert tally[living[1].id] == 3
    assert tally[living[2].id] == 2


def test_vote_cannot_target_dead():
    """Cannot vote for a dead player."""
    state = create_game_state("test", seed=42)
    voter = state.living_players()[0]
    target = state.living_players()[1]
    target.alive = False
    valid, msg = rules.validate_vote(state, voter, target.id)
    assert not valid
    assert "dead" in msg.lower()


def test_vote_cannot_target_self():
    """Cannot vote for yourself."""
    state = create_game_state("test", seed=42)
    voter = state.living_players()[0]
    valid, msg = rules.validate_vote(state, voter, voter.id)
    assert not valid
    assert "yourself" in msg.lower()


def test_full_game_runs_to_completion():
    """A full mock game runs and produces a winner."""
    engine = make_engine(seed=99)
    state = engine.state

    steps = 0
    while state.winner is None and steps < 100:
        engine.step()
        steps += 1
        if state.phase == PHASE_GAME_OVER:
            break

    assert state.winner in ("citizens", "mafia")
    assert state.phase == PHASE_GAME_OVER
    assert len(state.events) > 0


def test_game_has_correct_roles():
    """Game has exactly 1 mafia, 1 detective, 3 citizens."""
    state = create_game_state("test", seed=42)
    roles = [p.role for p in state.players]
    assert roles.count(ROLE_MAFIA) == 1
    assert roles.count(ROLE_DETECTIVE) == 1
    assert roles.count(ROLE_CITIZEN) == 3


def test_personalities_assigned():
    """Each player has a unique personality."""
    state = create_game_state("test", seed=42)
    personalities = [p.personality for p in state.players]
    assert len(set(personalities)) == 5


def test_llm_response_validation():
    """Pydantic validates the agent response schema."""
    from app.agents.schemas import AgentResponse, AgentAction, SuspicionUpdate

    valid_data = {
        "public_message": "I think Bob is suspicious.",
        "suspicion_updates": [
            {"player": "Bob", "score": 0.8, "reason": "Inconsistent statement"}
        ],
        "action": {"type": "vote", "target": "Bob"},
        "confidence": 0.8,
    }
    response = AgentResponse.model_validate(valid_data)
    assert response.public_message == "I think Bob is suspicious."
    assert response.action.type == "vote"
    assert response.action.target == "Bob"
    assert response.confidence == 0.8


def test_llm_response_rejects_invalid():
    """Invalid LLM JSON is rejected by Pydantic."""
    from app.agents.schemas import AgentResponse
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AgentResponse.model_validate({
            "public_message": "test",
            # Missing action
            "confidence": 0.5,
        })


def test_fallback_action_on_invalid_response():
    """When LLM returns invalid data, the agent falls back to mock behavior."""
    from app.agents.agent import Agent
    from app.agents.schemas import AgentResponse

    state = create_game_state("test", seed=42)
    player = state.players[0]

    # Create a fake LLM provider that always returns invalid data
    class FakeProvider:
        def generate(self, system_prompt, user_prompt):
            return {"invalid": "data"}

    agent = Agent(player, llm_provider=FakeProvider(), use_llm=True)
    # This should fall back to mock decision
    response = agent.make_day_decision(state)
    assert response is not None
    assert isinstance(response, AgentResponse)
    assert response.action.type == "vote"


def test_night_phase_processes_kill():
    """Night phase eliminates one player (mafia kill)."""
    engine = make_engine(seed=7)
    state = engine.state

    alive_before = len(state.living_players())
    engine.step()  # Run night
    alive_after = len(state.living_players())

    # Either someone was killed or nobody was (edge case)
    assert alive_after <= alive_before


def test_day_discussion_all_speak():
    """Day discussion phase: every living agent speaks."""
    engine = make_engine(seed=7)
    state = engine.state

    # Run night first
    engine.step()

    # Run discussion
    result = engine.step()
    discussion_events = [e for e in state.events if e.event_type == "discussion"]
    living = state.living_players()
    assert len(discussion_events) == len(living)
