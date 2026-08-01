"""Multi-turn chatbot with system prompt, windowed memory, and event log."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from collections import deque
import time
import uuid


class LLM(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


@dataclass
class MockLLM:
    """Deterministic offline LLM."""

    prefix: str = "[bot]"

    def complete(self, messages: list[dict[str, str]]) -> str:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"{self.prefix} {last_user[:200]}"


@dataclass
class ChatMessage:
    role: str
    content: str
    ts: float = field(default_factory=time.time)


@dataclass
class ChatSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[ChatMessage] = field(default_factory=list)
    max_turns: int = 20

    def append(self, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(role=role, content=content)
        self.messages.append(msg)
        # keep last max_turns*2 messages (user+assistant pairs)
        if len(self.messages) > self.max_turns * 2 + 1:
            system = [m for m in self.messages if m.role == "system"]
            rest = [m for m in self.messages if m.role != "system"]
            self.messages = system + rest[-(self.max_turns * 2) :]
        return msg

    def as_dicts(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.messages]


@dataclass
class EventLog:
    events: list[dict[str, Any]] = field(default_factory=list)

    def emit(self, kind: str, **payload: Any) -> None:
        self.events.append({"type": kind, "ts": time.time(), **payload})


@dataclass
class ChatBot:
    llm: LLM
    system_prompt: str = "You are a helpful assistant."
    events: EventLog = field(default_factory=EventLog)
    sessions: dict[str, ChatSession] = field(default_factory=dict)

    def new_session(self) -> ChatSession:
        s = ChatSession()
        s.append("system", self.system_prompt)
        self.sessions[s.session_id] = s
        self.events.emit("session_start", session_id=s.session_id)
        return s

    def chat(self, session_id: str, user_text: str) -> dict[str, Any]:
        if session_id not in self.sessions:
            raise KeyError(f"unknown session: {session_id}")
        s = self.sessions[session_id]
        s.append("user", user_text)
        self.events.emit("user_message", session_id=session_id, chars=len(user_text))
        reply = self.llm.complete(s.as_dicts())
        s.append("assistant", reply)
        self.events.emit("assistant_message", session_id=session_id, chars=len(reply))
        return {"session_id": session_id, "reply": reply, "turns": len([m for m in s.messages if m.role == "user"])}
