"""Tests for Phase 3: LLM provider abstraction."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pytest
from unittest.mock import patch, MagicMock

from app.llm.provider import LLMProvider, LLMError, NoAPIKeyError, get_provider
from app.llm.openrouter import OpenRouterProvider
from app.llm.groq import GroqProvider
from app.agents.schemas import AgentResponse


def test_provider_is_configured_false_without_key():
    """Provider reports not configured when no API key."""
    provider = OpenRouterProvider(api_key="")
    assert not provider.is_configured


def test_provider_is_configured_true_with_key():
    """Provider reports configured when API key is set."""
    provider = OpenRouterProvider(api_key="test_key")
    assert provider.is_configured


def test_no_api_key_raises_error():
    """Calling generate without API key raises NoAPIKeyError."""
    provider = OpenRouterProvider(api_key="")
    with pytest.raises(NoAPIKeyError):
        provider.generate("system", "user")


def test_openrouter_parses_json_response():
    """OpenRouter provider correctly parses a JSON response."""
    provider = OpenRouterProvider(api_key="test_key")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": '{"action": {"type": "vote", "target": "Bob"}, "confidence": 0.8}'}}
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = provider.generate("system", "user")
        assert result["action"]["type"] == "vote"
        assert result["action"]["target"] == "Bob"


def test_openrouter_parses_markdown_fenced_json():
    """Provider strips markdown code fences from LLM response."""
    provider = OpenRouterProvider(api_key="test_key")

    fenced_content = '```json\n{"action": {"type": "vote", "target": "Alice"}, "confidence": 0.7}\n```'
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": fenced_content}}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = provider.generate("system", "user")
        assert result["action"]["target"] == "Alice"


def test_openrouter_raises_on_invalid_json():
    """Provider raises LLMError when response is not valid JSON."""
    provider = OpenRouterProvider(api_key="test_key")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "This is not JSON at all."}}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(LLMError):
            provider.generate("system", "user")


def test_groq_provider_not_configured():
    """Groq provider reports not configured without key."""
    provider = GroqProvider(api_key="")
    assert not provider.is_configured


def test_get_provider_returns_none_when_not_configured():
    """Factory returns a provider instance even without keys (is_configured will be False)."""
    # With no env vars set, should still return an instance
    provider = get_provider()
    assert provider is not None
    assert isinstance(provider, LLMProvider)


def test_agent_retry_on_invalid_llm_response():
    """Agent retries with repair prompt on first LLM failure, then falls back to mock."""
    from app.agents.agent import Agent
    from app.game.state import create_game_state

    state = create_game_state("test_retry", seed=42)
    player = state.players[0]

    call_count = [0]

    class FailingProvider:
        @property
        def name(self):
            return "failing"

        @property
        def is_configured(self):
            return True

        def generate(self, system_prompt, user_prompt):
            call_count[0] += 1
            raise LLMError("Simulated failure")

    agent = Agent(player, llm_provider=FailingProvider(), use_llm=True)
    response = agent.make_day_decision(state)

    # Should have tried twice (first + retry), then fallen back to mock
    assert call_count[0] == 2
    assert response is not None
    assert isinstance(response, AgentResponse)
    assert response.action.type == "vote"
