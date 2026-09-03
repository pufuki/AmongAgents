"""Groq LLM provider — optional fallback provider.

Uses the Groq chat completions API with structured JSON output.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from app.llm.provider import LLMProvider, LLMError, NoAPIKeyError
from app.core.config import GROQ_API_KEY, GROQ_MODEL, LLM_TIMEOUT_SECONDS

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(LLMProvider):
    """Groq API provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key if api_key is not None else GROQ_API_KEY
        self._model = model if model is not None else GROQ_MODEL

    @property
    def name(self) -> str:
        return "groq"

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def generate(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.is_configured:
            raise NoAPIKeyError(
                "Groq API key not configured. Set GROQ_API_KEY in the environment."
            )

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 500,
            "response_format": {"type": "json_object"},
        }

        try:
            with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as client:
                response = client.post(GROQ_URL, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.TimeoutException:
            raise LLMError("Groq request timed out.")
        except httpx.HTTPStatusError as e:
            raise LLMError(f"Groq API error: {e.response.status_code} — {e.response.text[:200]}")
        except httpx.RequestError as e:
            raise LLMError(f"Groq network error: {e}")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise LLMError(f"Groq response parse error: {e}")

        return self._parse_json_response(content)

    def _parse_json_response(self, content: str) -> dict:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:])
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse Groq JSON response: {e}. Content: {content[:200]}")
