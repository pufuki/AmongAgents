"""Context builder: constructs role-safe LLM prompts for each agent.

CRITICAL: This module guarantees that agents never receive information
they should not know. The complete global game state is NEVER sent to any agent.
"""

from __future__ import annotations

from app.game.state import GameState, Player
from app.agents.personalities import get_personality_description
from app.core.constants import ROLE_MAFIA, ROLE_DETECTIVE


def build_day_context(state: GameState, player: Player) -> dict:
    """Build the context for a day-phase agent decision.

    Returns a dict with:
      - system_prompt: role and personality instructions
      - user_prompt: current visible game state and what the agent must decide
      - valid_targets: list of player names the agent can vote for
    """
    living = state.living_players()
    living_names = [p.name for p in living if p.id != player.id]

    # Public events from the current and previous rounds
    public_events = [
        e.to_dict() for e in state.events
        if e.public and e.round_number <= state.round_number
    ]

    # Recent discussion statements from this round
    recent_discussion = [
        d for d in state._discussion
        if d.get("round") == state.round_number and d.get("player_id") != player.id
    ]

    system_parts = [
        "You are playing a game of Mafia. You are an autonomous agent.",
        f"Your name is {player.name}.",
        f"Your personality is {player.personality}.",
        get_personality_description(player.personality),
    ]

    # Role-specific secret knowledge
    if player.role == ROLE_MAFIA:
        system_parts.append("You are the MAFIA. Your goal is to eliminate all citizens without being caught.")
        system_parts.append("You must blend in during the day. Accuse others to deflect suspicion.")
    elif player.role == ROLE_DETECTIVE:
        system_parts.append("You are the DETECTIVE. Your goal is to find the mafia through investigations.")
        if player.investigation_results:
            results_str = ", ".join(
                f"{state.get_player(tid).name}: {res}"
                for tid, res in player.investigation_results.items()
            )
            system_parts.append(f"Your investigation results so far: {results_str}")
        system_parts.append("You must be careful not to reveal your role too early.")
    else:
        system_parts.append("You are a CITIZEN. Your goal is to help identify and eliminate the mafia.")

    # Private suspicion summary
    if player.suspicions:
        susp_str = ", ".join(
            f"{state.get_player(pid).name}: {score:.2f}"
            for pid, score in sorted(player.suspicions.items(), key=lambda x: x[1], reverse=True)
            if state.get_player(pid) and state.get_player(pid).alive
        )
        system_parts.append(f"Your current suspicion scores: {susp_str}")

    system_prompt = " ".join(system_parts)

    # User prompt: what happened and what to decide
    user_parts = [
        f"=== Day {state.round_number} Discussion ===",
        f"Living players: {', '.join([p.name for p in living])}",
    ]

    if recent_discussion:
        user_parts.append("\nRecent statements:")
        for d in recent_discussion:
            user_parts.append(f"  {d['player_name']}: \"{d['message']}\"")

    if public_events:
        recent = public_events[-5:]
        user_parts.append("\nRecent events:")
        for e in recent:
            user_parts.append(f"  [{e['phase']}] {e['message']}")

    user_parts.append(
        "\nYou must now make your move. Respond with a JSON object containing:\n"
        "- public_message: a short statement (1-2 sentences) to share with the group\n"
        "- suspicion_updates: array of {player, score (0-1), reason} for players whose suspicion changed\n"
        "- action: {type: \"vote\", target: \"<player name>\"} — vote to eliminate a player\n"
        "- confidence: your confidence level (0-1)\n"
        f"\nValid vote targets: {', '.join(living_names)}"
    )

    user_prompt = "\n".join(user_parts)

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "valid_targets": living_names,
    }


def build_night_context(state: GameState, player: Player) -> dict:
    """Build context for a night-phase agent decision.

    Mafia chooses a kill target. Detective chooses an investigation target.
    Citizens do nothing at night.
    """
    living = state.living_players()
    living_names = [p.name for p in living if p.id != player.id]

    system_parts = [
        "You are playing a game of Mafia. You are an autonomous agent.",
        f"Your name is {player.name}.",
        f"Your personality is {player.personality}.",
        get_personality_description(player.personality),
    ]

    action_instruction = ""
    valid_targets = []

    if player.role == ROLE_MAFIA:
        system_parts.append("You are the MAFIA. It is night. Choose a player to eliminate.")
        action_instruction = (
            "Choose a target to eliminate tonight. Respond with JSON:\n"
            "- action: {type: \"kill\", target: \"<player name>\"}\n"
            "- suspicion_updates: any updates based on today's discussion\n"
            "- confidence: 0-1\n"
        )
        valid_targets = living_names
    elif player.role == ROLE_DETECTIVE:
        system_parts.append("You are the DETECTIVE. It is night. Choose a player to investigate.")
        if player.investigation_results:
            results_str = ", ".join(
                f"{state.get_player(tid).name}: {res}"
                for tid, res in player.investigation_results.items()
            )
            system_parts.append(f"Previous investigations: {results_str}")
        action_instruction = (
            "Choose a target to investigate tonight. Respond with JSON:\n"
            "- action: {type: \"investigate\", target: \"<player name>\"}\n"
            "- suspicion_updates: any updates\n"
            "- confidence: 0-1\n"
        )
        valid_targets = living_names
    else:
        # Citizens don't act at night
        return {
            "system_prompt": "",
            "user_prompt": "",
            "valid_targets": [],
            "skip": True,
        }

    system_prompt = " ".join(system_parts)

    user_parts = [
        f"=== Night {state.round_number} ===",
        f"Living players: {', '.join([p.name for p in living])}",
        f"\n{action_instruction}",
        f"Valid targets: {', '.join(valid_targets)}",
    ]

    user_prompt = "\n".join(user_parts)

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "valid_targets": valid_targets,
    }
