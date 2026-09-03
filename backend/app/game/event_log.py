"""Event logging for game state."""

from __future__ import annotations

from app.game.state import GameState


def log_night_begin(state: GameState, round_number: int) -> None:
    state.add_event(
        round_number=round_number,
        phase="night",
        event_type="night_begin",
        message=f"Night {round_number} begins. The town falls into silence.",
    )


def log_mafia_kill(state: GameState, round_number: int, target_name: str) -> None:
    state.add_event(
        round_number=round_number,
        phase="night",
        event_type="mafia_kill",
        message=f"{target_name} was eliminated during the night.",
        public=True,
    )


def log_detective_investigation(state: GameState, round_number: int,
                                 detective_name: str, target_name: str,
                                 result: str) -> None:
    """Log detective investigation. Public event notes the investigation happened,
    but the result is private (stored in detective's investigation_results)."""
    state.add_event(
        round_number=round_number,
        phase="night",
        event_type="detective_investigation",
        message=f"The detective investigated {target_name}.",
        public=True,
        metadata={"detective": detective_name, "target": target_name, "result": result},
    )


def log_day_begin(state: GameState, round_number: int) -> None:
    state.add_event(
        round_number=round_number,
        phase="day_discussion",
        event_type="day_begin",
        message=f"Day {round_number} begins. The town gathers to discuss.",
    )


def log_discussion(state: GameState, round_number: int,
                   player_name: str, message: str) -> None:
    state.add_event(
        round_number=round_number,
        phase="day_discussion",
        event_type="discussion",
        message=f"{player_name} spoke: \"{message}\"",
    )


def log_voting_begin(state: GameState, round_number: int) -> None:
    state.add_event(
        round_number=round_number,
        phase="day_voting",
        event_type="voting_begin",
        message="Voting begins. Each player casts their vote.",
    )


def log_vote(state: GameState, round_number: int,
             voter_name: str, target_name: str) -> None:
    state.add_event(
        round_number=round_number,
        phase="day_voting",
        event_type="vote",
        message=f"{voter_name} voted for {target_name}.",
    )


def log_elimination(state: GameState, round_number: int,
                    player_name: str, role: str) -> None:
    state.add_event(
        round_number=round_number,
        phase="day_result",
        event_type="elimination",
        message=f"{player_name} was eliminated by vote. They were the {role}.",
    )


def log_no_elimination(state: GameState, round_number: int) -> None:
    state.add_event(
        round_number=round_number,
        phase="day_result",
        event_type="no_elimination",
        message="No player was eliminated (tie or no votes).",
    )


def log_game_over(state: GameState, winner: str) -> None:
    state.add_event(
        round_number=state.round_number,
        phase="game_over",
        event_type="game_over",
        message=f"Game over. {winner.capitalize()} win!",
        metadata={"winner": winner},
    )


def log_nobody_killed(state: GameState, round_number: int) -> None:
    state.add_event(
        round_number=round_number,
        phase="night",
        event_type="no_kill",
        message="Nobody was eliminated during the night.",
    )
