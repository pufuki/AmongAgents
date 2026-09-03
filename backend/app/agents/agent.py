"""Agent: wraps a Player with decision-making capability.

Phase 1 uses deterministic mock behavior.
Phase 4 replaces this with LLM-backed decisions.
"""

from __future__ import annotations

import random
from typing import Optional

from app.game.state import GameState, Player
from app.agents.schemas import AgentResponse, NightActionResponse, AgentAction, SuspicionUpdate
from app.agents.context_builder import build_day_context, build_night_context
from app.agents.memory import update_suspicion, add_memory
from app.llm.prompts import BASE_SYSTEM, REPAIR_PROMPT, REPAIR_PROMPT_NIGHT


class Agent:
    """Wraps a Player and produces decisions for game phases."""

    def __init__(self, player: Player, llm_provider=None, use_llm: bool = False):
        self.player = player
        self.llm_provider = llm_provider
        self.use_llm = use_llm

    # ---- Day phase ----

    def make_day_decision(self, state: GameState) -> AgentResponse:
        """Produce a day-phase decision: public statement + vote."""
        context = build_day_context(state, self.player)

        if self.use_llm and self.llm_provider:
            response = self._llm_day_decision(state, context)
            if response is not None:
                self._apply_suspicion_updates(state, response)
                return response
            # Fall through to mock on failure

        return self._mock_day_decision(state, context)

    def _llm_day_decision(self, state: GameState, context: dict) -> Optional[AgentResponse]:
        """Call LLM provider for a day decision with one retry on invalid JSON.

        Returns None on failure (caller falls back to mock).
        """
        system_prompt = BASE_SYSTEM + " " + context["system_prompt"]
        user_prompt = context["user_prompt"]

        # First attempt
        try:
            raw = self.llm_provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            return AgentResponse.model_validate(raw)
        except Exception as e:
            add_memory(self.player, state.round_number, "llm_error",
                       f"LLM day decision first attempt failed: {e}")

        # Retry with repair prompt
        try:
            raw = self.llm_provider.generate(
                system_prompt=system_prompt,
                user_prompt=REPAIR_PROMPT,
            )
            return AgentResponse.model_validate(raw)
        except Exception as e:
            add_memory(self.player, state.round_number, "llm_error",
                       f"LLM day decision retry also failed: {e}")
            return None

    def _mock_day_decision(self, state: GameState, context: dict) -> AgentResponse:
        """Deterministic/mock day decision for Phase 1."""
        rng = random.Random(hash(self.player.id + str(state.round_number)))
        living = state.living_players()
        others = [p for p in living if p.id != self.player.id]

        # Generate a mock public statement based on personality
        message = self._mock_statement(rng, others)

        # Choose a vote target: highest suspicion, or random for chaotic
        if self.player.personality == "chaotic":
            target = rng.choice(others)
        else:
            # Vote for most suspicious living player
            suspects = [
                (p, self.player.suspicions.get(p.id, 0.3))
                for p in others
            ]
            suspects.sort(key=lambda x: x[1], reverse=True)
            target = suspects[0][0] if suspects else rng.choice(others)

        # Slight random suspicion adjustments
        suspicion_updates = []
        for p in others:
            delta = rng.uniform(-0.1, 0.1)
            new_score = max(0.0, min(1.0, self.player.suspicions.get(p.id, 0.3) + delta))
            self.player.suspicions[p.id] = round(new_score, 2)
            suspicion_updates.append(SuspicionUpdate(
                player=p.name,
                score=round(new_score, 2),
                reason="Adjusted based on discussion.",
            ))

        return AgentResponse(
            public_message=message,
            suspicion_updates=suspicion_updates,
            action=AgentAction(type="vote", target=target.name),
            confidence=round(rng.uniform(0.4, 0.8), 2),
        )

    def _mock_statement(self, rng: random.Random, others: list[Player]) -> str:
        """Generate a personality-flavored mock statement."""
        target = rng.choice(others) if others else self.player

        templates = {
            "analytical": [
                f"I've been tracking the statements. {target.name} seems inconsistent.",
                "Let's review the facts before we rush to a vote.",
                "The pattern of eliminations suggests the mafia is among us.",
            ],
            "aggressive": [
                f"I'm voting for {target.name}. We can't afford to wait!",
                f"{target.name} is acting suspicious. Let's end this now.",
                "Enough talk. Someone needs to be held accountable today.",
            ],
            "diplomatic": [
                "Let's hear everyone out before making a decision.",
                f"I'm not sure about {target.name}, but let's not be hasty.",
                "We should work together to find the truth.",
            ],
            "quiet": [
                "...",
                f"{target.name}. That's all I'll say.",
                "I have my suspicions. Let's vote.",
            ],
            "chaotic": [
                f"Maybe it's {target.name}... or maybe it's me! Who knows?",
                f"I changed my mind. {target.name} is definitely suspicious.",
                "What if we're all wrong? Think about it.",
            ],
        }
        choices = templates.get(self.player.personality, templates["analytical"])
        return rng.choice(choices)

    # ---- Night phase ----

    def make_night_decision(self, state: GameState) -> Optional[NightActionResponse]:
        """Produce a night-phase decision. Returns None if player doesn't act at night."""
        context = build_night_context(state, self.player)

        if context.get("skip"):
            return None

        if self.use_llm and self.llm_provider:
            response = self._llm_night_decision(state, context)
            if response is not None:
                self._apply_suspicion_updates_night(state, response)
                return response
            # Fall through to mock on failure

        return self._mock_night_decision(state, context)

    def _llm_night_decision(self, state: GameState, context: dict) -> Optional[NightActionResponse]:
        """Call LLM provider for a night decision with one retry on invalid JSON."""
        system_prompt = BASE_SYSTEM + " " + context["system_prompt"]
        user_prompt = context["user_prompt"]

        # First attempt
        try:
            raw = self.llm_provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            return NightActionResponse.model_validate(raw)
        except Exception as e:
            add_memory(self.player, state.round_number, "llm_error",
                       f"LLM night decision first attempt failed: {e}")

        # Retry with repair prompt
        try:
            raw = self.llm_provider.generate(
                system_prompt=system_prompt,
                user_prompt=REPAIR_PROMPT_NIGHT,
            )
            return NightActionResponse.model_validate(raw)
        except Exception as e:
            add_memory(self.player, state.round_number, "llm_error",
                       f"LLM night decision retry also failed: {e}")
            return None

    def _mock_night_decision(self, state: GameState, context: dict) -> NightActionResponse:
        rng = random.Random(hash(self.player.id + str(state.round_number) + "night"))
        valid_targets = context["valid_targets"]
        target_name = rng.choice(valid_targets) if valid_targets else ""

        if self.player.role == "mafia":
            action_type = "kill"
        elif self.player.role == "detective":
            action_type = "investigate"
        else:
            action_type = "none"

        return NightActionResponse(
            action=AgentAction(type=action_type, target=target_name),
            suspicion_updates=[],
            confidence=round(rng.uniform(0.5, 0.9), 2),
        )

    # ---- Suspicion update application ----

    def _apply_suspicion_updates(self, state: GameState, response: AgentResponse) -> None:
        for update in response.suspicion_updates:
            target = self._find_player_by_name(state, update.player)
            if target:
                update_suspicion(
                    self.player, target.id, update.score,
                    update.reason, state.round_number,
                )

    def _apply_suspicion_updates_night(self, state: GameState, response: NightActionResponse) -> None:
        for update in response.suspicion_updates:
            target = self._find_player_by_name(state, update.player)
            if target:
                update_suspicion(
                    self.player, target.id, update.score,
                    update.reason, state.round_number,
                )

    def _find_player_by_name(self, state: GameState, name: str) -> Optional[Player]:
        for p in state.players:
            if p.name == name:
                return p
        return None
