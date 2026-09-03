"""Agent memory: lightweight structured memory."""

from __future__ import annotations

from app.game.state import Player


def add_memory(player: Player, round_number: int, event_type: str,
               description: str, suspicion: float | None = None,
               target_id: str | None = None) -> None:
    """Add a structured memory entry to a player's private memory."""
    entry = {
        "round": round_number,
        "type": event_type,
        "description": description,
    }
    if suspicion is not None:
        entry["suspicion"] = suspicion
    if target_id is not None:
        entry["target"] = target_id
    player.memories.append(entry)


def update_suspicion(player: Player, target_id: str, score: float,
                     reason: str = "", round_number: int = 0) -> None:
    """Update a player's suspicion score for another player."""
    player.suspicions[target_id] = round(max(0.0, min(1.0, score)), 2)
    add_memory(
        player=player,
        round_number=round_number,
        event_type="suspicion_update",
        description=f"Updated suspicion of target to {score:.2f}. {reason}",
        suspicion=round(max(0.0, min(1.0, score)), 2),
        target_id=target_id,
    )


def get_suspicion_summary(player: Player) -> list[dict]:
    """Return a sorted list of (player_id, score) by suspicion descending."""
    items = [(pid, score) for pid, score in player.suspicions.items()]
    items.sort(key=lambda x: x[1], reverse=True)
    return [{"player_id": pid, "score": s} for pid, s in items]
