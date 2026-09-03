"""Phase execution: handles the step-by-step progression of game phases.

The engine processes one 'step' at a time. Each step is a meaningful game event:
  - Night actions (mafia kill, detective investigate)
  - Day discussion (each agent speaks)
  - Voting (each agent votes)
  - Vote resolution and elimination
  - Win condition check
"""

from __future__ import annotations

import random
from typing import Optional

from app.game.state import GameState, Player
from app.game import rules
from app.game import event_log
from app.agents.manager import AgentManager
from app.agents.schemas import AgentResponse, NightActionResponse
from app.core.constants import (
    PHASE_NIGHT,
    PHASE_DAY_DISCUSSION,
    PHASE_DAY_VOTING,
    PHASE_DAY_RESULT,
    PHASE_GAME_OVER,
    ROLE_MAFIA,
    ROLE_DETECTIVE,
)


class PhaseProcessor:
    """Processes individual phase steps. The engine delegates to this class."""

    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager

    # ---- Night phase ----

    def run_night(self, state: GameState) -> None:
        """Execute the complete night phase.

        1. Collect night decisions from all living agents.
        2. Process mafia kill.
        3. Process detective investigation.
        """
        event_log.log_night_begin(state, state.round_number)

        decisions = self.agent_manager.collect_night_decisions(state)

        # Process mafia kill
        mafia_killed = False
        for player_id, decision in decisions.items():
            if decision is None:
                continue
            player = state.get_player(player_id)
            if player is None or player.role != ROLE_MAFIA:
                continue

            target = self._find_player_by_name(state, decision.action.target)
            if target is None:
                # Fallback: kill a random living non-mafia player
                living_non_mafia = [
                    p for p in state.living_players() if p.role != ROLE_MAFIA
                ]
                if living_non_mafia:
                    target = random.choice(living_non_mafia)
                else:
                    continue

            valid, msg = rules.validate_night_mafia_target(state, player, target.id)
            if valid:
                target.alive = False
                event_log.log_mafia_kill(state, state.round_number, target.name)
                mafia_killed = True
            # If invalid, skip the kill (engine doesn't force it)

        if not mafia_killed:
            event_log.log_nobody_killed(state, state.round_number)

        # Process detective investigation
        for player_id, decision in decisions.items():
            if decision is None:
                continue
            player = state.get_player(player_id)
            if player is None or player.role != ROLE_DETECTIVE:
                continue

            target = self._find_player_by_name(state, decision.action.target)
            if target is None:
                # Fallback: investigate a random living player
                candidates = [
                    p for p in state.living_players()
                    if p.id != player.id
                ]
                if candidates:
                    target = random.choice(candidates)
                else:
                    continue

            valid, msg = rules.validate_night_detective_target(state, player, target.id)
            if valid:
                result = "mafia" if target.role == ROLE_MAFIA else "not_mafia"
                player.investigation_results[target.id] = result
                event_log.log_detective_investigation(
                    state, state.round_number,
                    player.name, target.name, result,
                )

    # ---- Day discussion phase ----

    def run_discussion(self, state: GameState) -> list[dict]:
        """Execute the day discussion phase. Each living agent speaks once.

        Returns list of {player_id, player_name, message} entries.
        """
        event_log.log_day_begin(state, state.round_number)

        decisions = self.agent_manager.collect_day_decisions(state)

        discussion_entries = []
        for player in state.living_players():
            decision = decisions.get(player.id)
            if decision is None:
                continue

            message = decision.public_message
            state._discussion.append({
                "round": state.round_number,
                "player_id": player.id,
                "player_name": player.name,
                "message": message,
            })
            event_log.log_discussion(state, state.round_number, player.name, message)
            discussion_entries.append({
                "player_id": player.id,
                "player_name": player.name,
                "message": message,
            })

        return discussion_entries

    # ---- Voting phase ----

    def run_voting(self, state: GameState) -> dict:
        """Execute the voting phase.

        Returns {"tally": {target_id: count}, "eliminated_id": str | None}.
        """
        event_log.log_voting_begin(state, state.round_number)

        # Re-collect decisions (the vote is part of the day decision)
        decisions = self.agent_manager.collect_day_decisions(state)

        state._votes = {}
        for player in state.living_players():
            decision = decisions.get(player.id)
            if decision is None:
                continue

            target = self._find_player_by_name(state, decision.action.target)
            if target is None:
                continue

            valid, msg = rules.validate_vote(state, player, target.id)
            if valid:
                state._votes[player.id] = target.id
                event_log.log_vote(state, state.round_number, player.name, target.name)

        tally = rules.count_votes(state)
        eliminated_id = rules.resolve_vote(tally)

        if eliminated_id:
            eliminated = state.get_player(eliminated_id)
            if eliminated:
                eliminated.alive = False
                event_log.log_elimination(
                    state, state.round_number, eliminated.name, eliminated.role,
                )
        else:
            event_log.log_no_elimination(state, state.round_number)

        return {"tally": tally, "eliminated_id": eliminated_id}

    # ---- Utility ----

    def _find_player_by_name(self, state: GameState, name: str) -> Player | None:
        for p in state.players:
            if p.name == name:
                return p
        return None
