#!/usr/bin/env python3
"""Run a full mock game to verify Phase 1 engine works end-to-end."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.manager import AgentManager
from app.game.engine import GameEngine


def main():
    print("=" * 60)
    print("AMONG AGENTS — Phase 1 Mock Game Test")
    print("=" * 60)

    agent_manager = AgentManager(use_llm=False)
    engine = GameEngine(agent_manager, seed=42)
    state = engine.create_game("test_game")

    print(f"\nGame created: {state.id}")
    print(f"Players:")
    for p in state.players:
        print(f"  {p.name} ({p.personality}) — role: {p.role}")

    print("\n--- Running game ---\n")

    step_count = 0
    while state.winner is None:
        step_count += 1
        result = engine.step()
        print(f"\n[Step {step_count}] Phase: {result['phase']} | Round: {result['round_number']} | Alive: {result['alive_count']}")
        for event in result["events"]:
            print(f"  → {event['message']}")
        if result["game_over"]:
            break

    print("\n" + "=" * 60)
    print(f"GAME OVER — Winner: {state.winner}")
    print(f"Total steps: {step_count}")
    print(f"Total events: {len(state.events)}")
    print("=" * 60)

    print("\nFinal player states:")
    for p in state.players:
        status = "ALIVE" if p.alive else "DEAD"
        print(f"  {p.name} ({p.personality}) — {p.role} — {status}")

    print("\nFull event log:")
    for e in state.events:
        print(f"  [{e.phase} R{e.round_number}] {e.message}")


if __name__ == "__main__":
    main()
