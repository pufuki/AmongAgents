"""Game state models and serialization."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from app.core.constants import (
    AGENT_NAMES,
    PERSONALITIES,
    ROLE_MAFIA,
    ROLE_DETECTIVE,
    ROLE_CITIZEN,
    NUM_MAFIA,
    NUM_DETECTIVE,
    NUM_CITIZENS,
)


@dataclass
class Player:
    id: str
    name: str
    personality: str
    role: str
    alive: bool = True
    # Detective investigation results: {target_id: "mafia" | "not_mafia"}
    investigation_results: dict[str, str] = field(default_factory=dict)
    # Private suspicion scores: {player_id: float}
    suspicions: dict[str, float] = field(default_factory=dict)
    # Private memories: list of structured entries
    memories: list[dict] = field(default_factory=list)

    def to_public_dict(self) -> dict:
        """Public-facing view: no role, no suspicions, no memories."""
        return {
            "id": self.id,
            "name": self.name,
            "personality": self.personality,
            "alive": self.alive,
        }

    def to_private_dict(self) -> dict:
        """Debug inspector view: includes everything."""
        return {
            "id": self.id,
            "name": self.name,
            "personality": self.personality,
            "role": self.role,
            "alive": self.alive,
            "investigation_results": dict(self.investigation_results),
            "suspicions": dict(self.suspicions),
            "memories": list(self.memories),
        }


@dataclass
class GameEvent:
    """A single logged event in the game timeline."""
    id: int
    round_number: int
    phase: str
    event_type: str
    message: str
    public: bool = True
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "round_number": self.round_number,
            "phase": self.phase,
            "event_type": self.event_type,
            "message": self.message,
            "public": self.public,
            "metadata": self.metadata,
        }


@dataclass
class GameState:
    id: str
    players: list[Player]
    phase: str = "waiting"
    round_number: int = 0
    events: list[GameEvent] = field(default_factory=list)
    winner: Optional[str] = None
    # Internal: night-phase actions collected
    _night_actions: dict = field(default_factory=dict)
    # Internal: day discussion statements collected
    _discussion: list[dict] = field(default_factory=list)
    # Internal: votes collected {voter_id: target_id}
    _votes: dict = field(default_factory=dict)
    # Internal: event counter
    _event_counter: int = 0

    def living_players(self) -> list[Player]:
        return [p for p in self.players if p.alive]

    def living_mafia(self) -> list[Player]:
        return [p for p in self.living_players() if p.role == ROLE_MAFIA]

    def living_citizens_and_detective(self) -> list[Player]:
        return [p for p in self.living_players() if p.role != ROLE_MAFIA]

    def get_player(self, player_id: str) -> Optional[Player]:
        for p in self.players:
            if p.id == player_id:
                return p
        return None

    def add_event(self, round_number: int, phase: str, event_type: str,
                  message: str, public: bool = True, metadata: dict = None) -> GameEvent:
        self._event_counter += 1
        event = GameEvent(
            id=self._event_counter,
            round_number=round_number,
            phase=phase,
            event_type=event_type,
            message=message,
            public=public,
            metadata=metadata or {},
        )
        self.events.append(event)
        return event

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "phase": self.phase,
            "round_number": self.round_number,
            "players": [p.to_public_dict() for p in self.players],
            "events": [e.to_dict() for e in self.events if e.public],
            "winner": self.winner,
            "alive_count": len(self.living_players()),
        }

    def to_debug_dict(self) -> dict:
        return {
            "id": self.id,
            "phase": self.phase,
            "round_number": self.round_number,
            "players": [p.to_private_dict() for p in self.players],
            "events": [e.to_dict() for e in self.events],
            "winner": self.winner,
            "alive_count": len(self.living_players()),
        }


def create_game_state(game_id: str, seed: Optional[int] = None) -> GameState:
    """Create a new game with shuffled roles and personalities."""
    rng = random.Random(seed)

    roles = (
        [ROLE_MAFIA] * NUM_MAFIA
        + [ROLE_DETECTIVE] * NUM_DETECTIVE
        + [ROLE_CITIZEN] * NUM_CITIZENS
    )
    rng.shuffle(roles)

    personalities = list(PERSONALITIES)
    rng.shuffle(personalities)

    players = []
    for i, name in enumerate(AGENT_NAMES):
        player = Player(
            id=f"player_{i}",
            name=name,
            personality=personalities[i],
            role=roles[i],
        )
        # Initialize suspicion scores for all other players
        for j in range(len(AGENT_NAMES)):
            if j != i:
                player.suspicions[f"player_{j}"] = round(rng.uniform(0.2, 0.4), 2)
        players.append(player)

    return GameState(id=game_id, players=players)
