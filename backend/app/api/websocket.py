"""WebSocket handler for live game events."""

from __future__ import annotations

import asyncio
import json
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db import persistence

router = APIRouter()

# Active WebSocket connections per game
_connections: Dict[str, list[WebSocket]] = {}


@router.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """WebSocket connection for live game updates.

    The frontend connects and receives push notifications when
    the game state changes (via /next or /autoplay).
    """
    await websocket.accept()

    if game_id not in _connections:
        _connections[game_id] = []
    _connections[game_id].append(websocket)

    try:
        # Send current state on connect
        db = SessionLocal()
        try:
            state = persistence.load_game(db, game_id)
            if state:
                await websocket.send_json({
                    "type": "state",
                    "data": state.to_public_dict(),
                })
        finally:
            db.close()

        # Keep connection alive, listen for messages
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if game_id in _connections:
            _connections[game_id].remove(websocket)
            if not _connections[game_id]:
                del _connections[game_id]


async def broadcast_event(game_id: str, event: dict):
    """Broadcast an event to all connected clients for a game."""
    if game_id not in _connections:
        return

    message = json.dumps({"type": "event", "data": event})
    dead = []
    for ws in _connections[game_id]:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)

    for ws in dead:
        _connections[game_id].remove(ws)
