"""Application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()

# LLM Provider settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./among_agents.db")

# API timeout
LLM_TIMEOUT_SECONDS = 30
