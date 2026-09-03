"""Game rules: win conditions and action validation."""

from __future__ import annotations

from app.core.constants import ROLE_MAFIA
from app.game.state import GameState, Player


def check_winner(state: GameState) -> str | None:
    """Determine if the game has ended and who won.

    Returns "citizens", "mafia", or None if game continues.
    """
    living_mafia = state.living_mafia()
    living_non_mafia = [p for p in state.living_players() if p.role != ROLE_MAFIA]

    if len(living_mafia) == 0:
        return "citizens"

    if len(living_mafia) >= len(living_non_mafia):
        return "mafia"

    return None


def validate_night_mafia_target(state: GameState, actor: Player, target_id: str) -> tuple[bool, str]:
    """Validate mafia's night kill target."""
    if not actor.alive:
        return False, "Dead agents cannot act."
    if actor.role != ROLE_MAFIA:
        return False, "Only the mafia can choose a night target."
    target = state.get_player(target_id)
    if target is None:
        return False, "Target does not exist."
    if not target.alive:
        return False, "Cannot target a dead player."
    if target.id == actor.id:
        return False, "Cannot target yourself."
    return True, ""


def validate_night_detective_target(state: GameState, actor: Player, target_id: str) -> tuple[bool, str]:
    """Validate detective's night investigation target."""
    if not actor.alive:
        return False, "Dead agents cannot act."
    if actor.role != "detective":
        return False, "Only the detective can investigate."
    target = state.get_player(target_id)
    if target is None:
        return False, "Target does not exist."
    if not target.alive:
        return False, "Cannot investigate a dead player."
    if target.id == actor.id:
        return False, "Cannot investigate yourself."
    return True, ""


def validate_vote(state: GameState, voter: Player, target_id: str) -> tuple[bool, str]:
    """Validate a day vote."""
    if not voter.alive:
        return False, "Dead agents cannot vote."
    target = state.get_player(target_id)
    if target is None:
        return False, "Target does not exist."
    if not target.alive:
        return False, "Cannot vote for a dead player."
    if target.id == voter.id:
        return False, "Cannot vote for yourself."
    return True, ""


def count_votes(state: GameState) -> dict[str, int]:
    """Count all collected votes and return {target_id: count}."""
    tally: dict[str, int] = {}
    for voter_id, target_id in state._votes.items():
        tally[target_id] = tally.get(target_id, 0) + 1
    return tally


def resolve_vote(tally: dict[str, int]) -> str | None:
    """Determine the eliminated player from vote tally.

    In case of a tie, pick randomly among tied players.
    Returns target_id or None if no votes.
    """
    if not tally:
        return None

    max_votes = max(tally.values())
    tied = [pid for pid, count in tally.items() if count == max_votes]

    import random
    return random.choice(tied)
