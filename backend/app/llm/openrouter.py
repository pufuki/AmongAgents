"""OpenRouter LLM provider.

Uses the OpenRouter chat completions API with structured JSON output.
API key is loaded ONLY from environment variables — never hardcoded,
never sent to the frontend.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from app.llm.provider import LLMProvider, LLMError, NoAPIKeyError
from app.core.config import OPENROUTER_API_KEY, OPENROUTER_MODEL, LLM_TIMEOUT_SECONDS

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key if api_key is not None else OPENROUTER_API_KEY
        self._model = model if model is not None else OPENROUTER_MODEL

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def generate(self, system_prompt: str, user_prompt: str) -> dict:
        """Send a chat completion request and return parsed JSON.

        Returns a dict parsed from the LLM's response content.
        Raises LLMError on failure, NoAPIKeyError if no key.
        """
        if not self.is_configured:
            raise NoAPIKeyError(
                "OpenRouter API key not configured. Set OPENROUTER_API_KEY in the environment."
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
        }

        try:
            with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as client:
                response = client.post(OPENROUTER_URL, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.TimeoutException:
            raise LLMError("OpenRouter request timed out.")
        except httpx.HTTPStatusError as e:
            raise LLMError(f"OpenRouter API error: {e.response.status_code} — {e.response.text[:200]}")
        except httpx.RequestError as e:
            raise LLMError(f"OpenRouter network error: {e}")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise LLMError(f"OpenRouter response parse error: {e}")

        return self._parse_json_response(content)

    def _parse_json_response(self, content: str) -> dict:
        """Extract and parse JSON from the LLM response content.

        Handles cases where the model wraps JSON in markdown code blocks
        or adds extra text.
        """
        # Strip markdown code fences if present
        cleaned = content.strip()
        if cleaned.startswith("```"):
            # Remove first line (```json or ```)
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:])
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse LLM JSON response: {e}. Content: {content[:200]}")
