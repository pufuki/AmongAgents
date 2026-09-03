"""Agent manager: coordinates agent decisions across the game.

Automatically detects LLM provider from environment. If an API key is
configured, agents use LLM-backed decisions. If not, they fall back to
deterministic mock behavior.
"""

from __future__ import annotations

from app.game.state import GameState, Player
from app.agents.agent import Agent
from app.agents.schemas import AgentResponse, NightActionResponse


class AgentManager:
    """Creates and manages Agent instances for a game."""

    def __init__(self, llm_provider=None, use_llm: bool = False):
        # Auto-detect provider from environment if none explicitly provided
        if llm_provider is None and use_llm:
            from app.llm.provider import get_provider
            llm_provider = get_provider()
            # If provider isn't configured, disable LLM mode
            if llm_provider is not None and not llm_provider.is_configured:
                use_llm = False

        self.llm_provider = llm_provider
        self.use_llm = use_llm
        self.agents: dict[str, Agent] = {}

    def initialize(self, state: GameState) -> None:
        """Create Agent wrappers for all players in the game state."""
        self.agents = {}
        for player in state.players:
            self.agents[player.id] = Agent(
                player=player,
                llm_provider=self.llm_provider,
                use_llm=self.use_llm,
            )

    def get_agent(self, player_id: str) -> Agent | None:
        return self.agents.get(player_id)

    def collect_day_decisions(self, state: GameState) -> dict[str, AgentResponse]:
        """Collect a day-phase decision from each living agent.

        Returns {player_id: AgentResponse}.
        """
        decisions = {}
        for player in state.living_players():
            agent = self.agents.get(player.id)
            if agent is None:
                continue
            decisions[player.id] = agent.make_day_decision(state)
        return decisions

    def collect_night_decisions(self, state: GameState) -> dict[str, NightActionResponse | None]:
        """Collect night-phase decisions from living agents.

        Returns {player_id: NightActionResponse or None}.
        Citizens return None (they don't act at night).
        """
        decisions = {}
        for player in state.living_players():
            agent = self.agents.get(player.id)
            if agent is None:
                continue
            decisions[player.id] = agent.make_night_decision(state)
        return decisions
