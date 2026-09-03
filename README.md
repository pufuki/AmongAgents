# AMONG AGENTS

**Multi-Agent Social Deduction Simulation**

A web-based simulation where 5 autonomous AI agents play a complete game of Mafia against each other. Each agent has a secret role, private memory, maintains suspicion scores, and makes strategic decisions independently.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                 FRONTEND (React + Vite)                │
│  Header · GameBoard · AgentCard · EventTimeline       │
│  DiscussionPanel · AgentInspector · GameControls      │
└─────────────────────────┬────────────────────────────┘
                          │ REST API
┌─────────────────────────▼────────────────────────────┐
│              BACKEND (FastAPI + Python)                │
│  ┌──────────┐  ┌───────────┐  ┌────────────────────┐  │
│  │   API    │  │   Game    │  │      Agents        │  │
│  │  Routes  │→ │  Engine   │← │ Manager + Context  │  │
│  └──────────┘  │  Rules    │  │ Builder + Memory   │  │
│                │  Phases   │  └─────────┬──────────┘  │
│                └─────┬─────┘            │             │
│                      │        ┌─────────▼──────────┐  │
│                ┌─────▼─────┐   │   LLM Provider     │  │
│                │    DB     │   │ (OpenRouter / Groq)│  │
│                │  SQLite   │   └────────────────────┘  │
│                └───────────┘                           │
└───────────────────────────────────────────────────────┘
```

### Backend Structure

```
backend/
  app/
    main.py              # FastAPI app entry point
    api/
      routes_games.py    # REST endpoints for game control
      routes_agents.py   # Agent inspection endpoints
      websocket.py       # WebSocket for live events
    core/
      config.py          # Environment configuration
      constants.py       # Game constants (roles, phases, etc.)
    game/
      engine.py          # Authoritative game controller
      state.py           # Game state + player models
      rules.py           # Win conditions + action validation
      phases.py          # Phase execution (night, day, voting)
      event_log.py       # Event logging functions
    agents/
      agent.py           # Agent decision-making (mock + LLM)
      manager.py         # Coordinates agent decisions
      context_builder.py # Role-safe LLM prompt builder
      memory.py          # Lightweight structured memory
      personalities.py   # Personality definitions
      schemas.py         # Pydantic models for LLM responses
    llm/
      provider.py        # Provider interface + factory
      openrouter.py      # OpenRouter provider
      groq.py            # Groq provider (fallback)
      prompts.py         # Prompt templates
    db/
      database.py        # SQLAlchemy setup
      models.py          # ORM models
      persistence.py     # Save/load game state
  tests/
    test_engine.py       # Engine + rules tests
    test_db.py           # Database persistence tests
    test_llm.py          # LLM provider tests
  requirements.txt
  .env.example
  run_test_game.py       # Headless mock game runner
```

### Frontend Structure

```
src/
  App.tsx                 # Main app (state management, API calls)
  index.css               # Global styles (plain CSS, cinematic dark theme)
  components/
    Header.tsx            # Title, phase indicator, round counter
    GameBoard.tsx         # Layout wrapper for game panels
    AgentCard.tsx         # Player card (name, personality, alive/dead)
    EventTimeline.tsx     # Chronological event log
    DiscussionPanel.tsx   # Agent public statements
    AgentInspector.tsx    # Agent detail view (public + debug)
    GameControls.tsx      # Start/Next/AutoPlay/Reset buttons
```

---

## Features

- **5 autonomous AI agents** with unique personalities (analytical, aggressive, diplomatic, quiet, chaotic)
- **Secret roles**: 1 Mafia, 1 Detective, 3 Citizens — randomly assigned, independent of personality
- **Private agent memory**: suspicion scores, investigation results, structured event memories
- **Role-safe context building**: agents never receive information they shouldn't have
- **Deterministic game engine**: controls all rules, validates actions, determines winner
- **LLM provider abstraction**: OpenRouter (primary) or Groq (fallback), swappable without touching game logic
- **Cost-optimized**: one LLM call per agent turn, structured JSON output, retry + fallback
- **SQLite persistence**: games and events saved to database
- **Cinematic dark UI**: charcoal/burgundy/gold theme, smooth animations
- **Debug inspector**: after game ends, reveal roles, suspicions, and memories

---

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
npm install
```

---

## Environment Variables

Copy the example file and fill in your API key:

```bash
cp backend/.env.example backend/.env
```

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | Which LLM provider to use (`openrouter` or `groq`) | `openrouter` |
| `OPENROUTER_API_KEY` | OpenRouter API key (required for AI agents) | (empty) |
| `OPENROUTER_MODEL` | Model to use | `openrouter/free` |
| `GROQ_API_KEY` | Groq API key (optional fallback) | (empty) |
| `GROQ_MODEL` | Groq model name | `llama-3.1-8b-instant` |
| `DATABASE_URL` | SQLite database path | `sqlite:///./among_agents.db` |

**The app runs without an API key** — agents fall back to deterministic mock behavior. You'll see a banner: "AI provider is not configured."

---

## Running the Backend

```bash
cd backend
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

---

## Running the Frontend

```bash
npm run dev
```

The frontend runs on `http://localhost:5173` and connects to the backend on port 8000.

---

## How AI Agents Work

1. **Context Builder** — Before each agent's turn, a role-safe context is built containing only the information that agent is allowed to know:
   - Public: alive players, discussion history, eliminations
   - Private: own role, own suspicion scores, own memories
   - Secret: mafia knows who they are; detective knows investigation results

2. **Single LLM Call** — One request returns structured JSON:
   ```json
   {
     "public_message": "Bob contradicted his earlier statement.",
     "suspicion_updates": [{"player": "Bob", "score": 0.82, "reason": "Changed accusation"}],
     "action": {"type": "vote", "target": "Bob"},
     "confidence": 0.82
   }
   ```

3. **Validation** — The backend validates the response with Pydantic. If invalid:
   - Retry once with a repair prompt
   - If still invalid, use a deterministic fallback action
   - Log the error (never crash)

4. **Engine Authority** — The LLM never modifies game state directly. The engine validates all actions (can't target dead players, can't vote for yourself, etc.) and applies them.

---

## API Cost Optimization

- **One LLM call per agent turn** — not multiple calls per decision
- **Structured JSON output** — no chain-of-thought, no extra tokens
- **Concise prompts** — system + user prompt kept short
- **Short public messages** — agents produce 1-2 sentence statements
- **Mock fallback** — when no API key is configured, agents use deterministic behavior (zero API cost)
- **No continuous polling** — LLM is only called when it's an agent's turn to make a meaningful decision

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/games` | Create a new game |
| `GET` | `/games/{game_id}` | Get public game state (`?debug=true` for private) |
| `POST` | `/games/{game_id}/next` | Advance game by one meaningful event |
| `POST` | `/games/{game_id}/autoplay` | Enable/disable autoplay |
| `POST` | `/games/{game_id}/reset` | Reset the game |
| `GET` | `/games/{game_id}/events` | Get chronological events |
| `GET` | `/agents/{game_id}` | Get all agents' states |
| `GET` | `/agents/{game_id}/{player_id}` | Get specific agent state |
| `WS` | `/ws/{game_id}` | WebSocket for live events |

---

## Manual Testing Checklist

1. **Start backend**: `cd backend && PYTHONPATH=. uvicorn app.main:app --port 8000`
2. **Start frontend**: `npm run dev`
3. **Open browser**: `http://localhost:5173`
4. **Verify no-API-key banner** appears (if no key configured)
5. **Click "Start New Game"** — 5 player cards appear with names and personalities
6. **Click "Next Event"** repeatedly — watch night → discussion → voting → result cycle
7. **Click "Auto Play"** — game progresses automatically with delays
8. **Click a player card** — agent inspector shows public info
9. **Wait for game to end** — winner banner appears
10. **Toggle "Debug Mode"** — roles, suspicions, and memories become visible
11. **Click "Reset"** — new game starts with fresh roles
12. **Run tests**: `cd backend && PYTHONPATH=. python3 -m pytest tests/ -v`
13. **Run headless game**: `cd backend && PYTHONPATH=. python3 run_test_game.py`

---

## Limitations

- **No real API key testing**: LLM-backed agent decisions could not be verified without a live OpenRouter/Groq key. Mock agent behavior is fully tested.
- **Single-game sessions**: The MVP supports one game at a time per browser tab. No multi-game lobby.
- **5 players only**: The game is configured for exactly 5 agents (1 mafia, 1 detective, 3 citizens). Not configurable at runtime.
- **No authentication**: No login system, as specified.
- **SQLite**: Uses local SQLite, not a cloud database. Data persists locally only.
- **WebSocket is optional**: The frontend uses REST polling for simplicity. WebSocket is available but not required.
- **No chain-of-thought storage**: Per spec, hidden reasoning is never stored. Only observable facts and structured conclusions.
