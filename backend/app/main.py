"""FastAPI application entry point."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_games import router as games_router
from app.api.routes_agents import router as agents_router
from app.api.websocket import router as ws_router
from app.db.database import init_db
from app.core.config import OPENROUTER_API_KEY, GROQ_API_KEY, LLM_PROVIDER

app = FastAPI(
    title="Among Agents",
    description="Multi-Agent Social Deduction Simulation",
    version="1.0.0",
)

# CORS: allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(games_router)
app.include_router(agents_router)
app.include_router(ws_router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    """Health check and API status."""
    api_configured = bool(OPENROUTER_API_KEY or GROQ_API_KEY)
    return {
        "name": "Among Agents",
        "version": "1.0.0",
        "ai_configured": api_configured,
        "provider": LLM_PROVIDER,
        "message": (
            "AI provider is configured."
            if api_configured
            else "AI provider is not configured. Add OPENROUTER_API_KEY to the backend environment."
        ),
    }


@app.get("/health")
def health():
    return {"status": "ok"}
