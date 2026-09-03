"""Game engine: the authoritative controller of all game rules and flow.

The engine is deterministic. It controls phases, validates actions,
updates state, and checks the winner. The LLM only generates decisions
and communication — the engine validates and applies them.

The engine processes one 'step' at a time. Each step is a meaningful event:
  Step 1: Night phase (mafia kill + detective investigate)
  Step 2: Day discussion (all agents speak)
  Step 3: Day voting (all agents vote + elimination)
  Step 4: Check win condition
  Repeat until game over.
"""

from __future__ import annotations

import uuid
from typing import Optional

from app.game.state import GameState, create_game_state
from app.game.phases import PhaseProcessor
from app.game import rules
from app.game import event_log
from app.agents.manager import AgentManager
from app.core.constants import (
    PHASE_NIGHT,
    PHASE_DAY_DISCUSSION,
    PHASE_DAY_VOTING,
    PHASE_DAY_RESULT,
    PHASE_GAME_OVER,
)


class GameEngine:
    """The authoritative game controller."""

    def __init__(self, agent_manager: AgentManager, seed: int | None = None):
        self.agent_manager = agent_manager
        self.seed = seed
        self.state: GameState | None = None
        self.processor = PhaseProcessor(agent_manager)

    def create_game(self, game_id: str | None = None) -> GameState:
        """Create a new game with randomized roles."""
        if game_id is None:
            game_id = str(uuid.uuid4())[:8]
        self.state = create_game_state(game_id, seed=self.seed)
        self.agent_manager.initialize(self.state)
        self.state.phase = PHASE_NIGHT
        self.state.round_number = 1
        return self.state

    def step(self) -> dict:
        """Advance the game by one meaningful event.

        Returns a dict with:
          - phase: the phase that was just executed
          - round_number: current round
          - events: list of new events from this step
          - winner: "citizens" | "mafia" | None
          - game_over: bool
        """
        if self.state is None:
            raise RuntimeError("No game created. Call create_game() first.")

        if self.state.winner is not None:
            return self._step_result(PHASE_GAME_OVER, [], True)

        phase = self.state.phase
        events_before = len(self.state.events)

        if phase == PHASE_NIGHT:
            self.processor.run_night(self.state)
            self.state.phase = PHASE_DAY_DISCUSSION
            # Check win after night kill
            winner = rules.check_winner(self.state)
            if winner:
                self._end_game(winner)

        elif phase == PHASE_DAY_DISCUSSION:
            self.processor.run_discussion(self.state)
            self.state.phase = PHASE_DAY_VOTING

        elif phase == PHASE_DAY_VOTING:
            self.processor.run_voting(self.state)
            self.state.phase = PHASE_DAY_RESULT
            # Check win after vote elimination
            winner = rules.check_winner(self.state)
            if winner:
                self._end_game(winner)

        elif phase == PHASE_DAY_RESULT:
            # Advance to next night
            self.state.round_number += 1
            self.state.phase = PHASE_NIGHT

        new_events = [e.to_dict() for e in self.state.events[events_before:]]

        return self._step_result(phase, new_events, self.state.winner is not None)

    def run_full_game(self) -> dict:
        """Run the entire game to completion. Returns final state dict.

        Used for testing and headless runs.
        """
        if self.state is None:
            self.create_game()

        while self.state.winner is None:
            self.step()
            if self.state.phase == PHASE_GAME_OVER:
                break

        return self.state.to_public_dict()

    def get_state(self) -> GameState:
        if self.state is None:
            raise RuntimeError("No game created.")
        return self.state

    def reset(self) -> GameState:
        """Reset the game with a new state."""
        return self.create_game()

    def _end_game(self, winner: str) -> None:
        self.state.winner = winner
        self.state.phase = PHASE_GAME_OVER
        event_log.log_game_over(self.state, winner)

    def _step_result(self, phase: str, events: list[dict], game_over: bool) -> dict:
        return {
            "phase": phase,
            "round_number": self.state.round_number,
            "events": events,
            "winner": self.state.winner,
            "game_over": game_over,
            "alive_count": len(self.state.living_players()),
        }
