"""Agent schemas: structured LLM response models."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class SuspicionUpdate(BaseModel):
    player: str = Field(..., description="Name of the player")
    score: float = Field(..., ge=0.0, le=1.0, description="Suspicion score 0-1")
    reason: str = Field("", description="Short reason for the suspicion change")


class AgentAction(BaseModel):
    type: str = Field(..., description="Action type: vote, investigate, kill")
    target: str = Field(..., description="Name of the target player")


class AgentResponse(BaseModel):
    """Structured response from an agent's LLM call."""
    public_message: str = Field("", description="Short public statement")
    suspicion_updates: list[SuspicionUpdate] = Field(default_factory=list)
    action: AgentAction = Field(..., description="The agent's intended action")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Confidence 0-1")


class NightActionResponse(BaseModel):
    """Simplified response for night-phase actions (no public message)."""
    action: AgentAction = Field(..., description="The agent's intended night action")
    suspicion_updates: list[SuspicionUpdate] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
