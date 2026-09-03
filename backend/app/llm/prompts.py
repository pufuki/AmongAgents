"""Prompt templates for LLM agent decisions.

Keeps prompts concise to minimize API cost.
"""

from __future__ import annotations

# System-level instruction appended to all agent prompts
BASE_SYSTEM = (
    "You are an autonomous AI agent playing a game of Mafia (social deduction). "
    "You must respond with ONLY a valid JSON object. No markdown, no explanation outside the JSON. "
    "The JSON must match the requested schema exactly."
)

# Repair prompt used when the first LLM response is invalid JSON
REPAIR_PROMPT = (
    "Your previous response was not valid JSON or did not match the required schema. "
    "Please respond again with ONLY a valid JSON object matching this schema:\n"
    "{\n"
    '  "public_message": "short statement (1-2 sentences)",\n'
    '  "suspicion_updates": [{"player": "name", "score": 0.0-1.0, "reason": "short reason"}],\n'
    '  "action": {"type": "vote", "target": "player name"},\n'
    '  "confidence": 0.0-1.0\n'
    "}\n"
    "Respond with ONLY the JSON. No other text."
)

REPAIR_PROMPT_NIGHT = (
    "Your previous response was not valid JSON or did not match the required schema. "
    "Please respond again with ONLY a valid JSON object matching this schema:\n"
    "{\n"
    '  "action": {"type": "kill" or "investigate", "target": "player name"},\n'
    '  "suspicion_updates": [{"player": "name", "score": 0.0-1.0, "reason": "short reason"}],\n'
    '  "confidence": 0.0-1.0\n'
    "}\n"
    "Respond with ONLY the JSON. No other text."
)
