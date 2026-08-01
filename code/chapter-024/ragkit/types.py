"""Contracts for production RAG."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Trust(str, Enum):
    SYSTEM = "system"
    USER = "user"
    EVIDENCE = "evidence"  # retrieved — untrusted
    MEMORY = "memory"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id required")


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    rank: int = 0
    ranker_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "id": self.id,
            "score": round(self.score, 6),
            "ranker_score": None if self.ranker_score is None else round(self.ranker_score, 6),
            "text": self.text,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class Citation:
    index: int
    doc_id: str
    title: str
    snippet: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def marker(self) -> str:
        return f"[{self.index}]"


@dataclass
class Message:
    role: str
    content: str
    trust: Trust = Trust.USER

    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role, "content": self.content, "trust": self.trust.value}


@dataclass
class AssembledPrompt:
    system: str
    user: str
    messages: list[Message]
    citations: list[Citation]
    evidence_ids: list[str]
    token_estimate: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "user": self.user,
            "messages": [m.to_dict() for m in self.messages],
            "citations": [c.to_dict() for c in self.citations],
            "evidence_ids": self.evidence_ids,
            "token_estimate": self.token_estimate,
        }


@dataclass
class RAGAnswer:
    answer: str
    citations: list[Citation]
    grounded: bool
    retrieved: list[RetrievedChunk]
    prompt: AssembledPrompt | None
    memory_turns: int
    model_id: str
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "grounded": self.grounded,
            "citations": [c.to_dict() for c in self.citations],
            "retrieved": [r.to_dict() for r in self.retrieved],
            "memory_turns": self.memory_turns,
            "model_id": self.model_id,
            "diagnostics": self.diagnostics,
            "prompt": None if self.prompt is None else self.prompt.to_dict(),
        }
