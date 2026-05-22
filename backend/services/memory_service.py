"""
services/memory_service.py
In-memory session store for short-term multi-turn conversation history.
Holds the last MAX_TURNS turns per session_id. Thread-safe via a lock.
"""
from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Deque

MAX_TURNS = 5


@dataclass
class Turn:
    role: str   # "user" or "assistant"
    content: str


@dataclass
class Session:
    turns: Deque[Turn] = field(default_factory=lambda: deque(maxlen=MAX_TURNS))

    def add(self, role: str, content: str) -> None:
        self.turns.append(Turn(role=role, content=content))

    def to_context_string(self) -> str:
        if not self.turns:
            return ""
        lines = []
        for turn in self.turns:
            prefix = "User" if turn.role == "user" else "Assistant"
            lines.append(f"{prefix}: {turn.content[:600]}")
        return "\n".join(lines)


class MemoryService:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def get_or_create(self, session_id: str) -> Session:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = Session()
            return self._sessions[session_id]

    def add_turn(self, session_id: str, role: str, content: str) -> None:
        self.get_or_create(session_id).add(role, content)

    def get_context(self, session_id: str) -> str:
        with self._lock:
            session = self._sessions.get(session_id)
            return session.to_context_string() if session else ""

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


# Module-level singleton shared across requests
memory = MemoryService()
