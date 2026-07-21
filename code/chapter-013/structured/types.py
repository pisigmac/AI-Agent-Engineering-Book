"""Error types and attempt logging for structured outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class StructuredOutputError(Exception):
    """Base error for structured output pipeline."""

    def __init__(self, message: str, *, code: str = "structured_error") -> None:
        super().__init__(message)
        self.code = code


class StructureParseError(StructuredOutputError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="parse_error")


class StructureValidationError(StructuredOutputError):
    def __init__(self, message: str, *, errors: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message, code="validation_error")
        self.errors = errors or []


class StructureExhaustedError(StructuredOutputError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="repairs_exhausted")


@dataclass
class AttemptRecord:
    index: int
    raw_text: str
    ok: bool
    error_code: str | None = None
    error_message: str | None = None
    parsed: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "ok": self.ok,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "parsed": self.parsed,
            "raw_preview": self.raw_text[:240],
        }


@dataclass
class StructuredResult:
    """Outcome of a structured completion attempt sequence."""

    value: Any | None
    error: StructuredOutputError | None
    attempts: list[AttemptRecord] = field(default_factory=list)
    model_name: str = ""

    @property
    def ok(self) -> bool:
        return self.value is not None and self.error is None

    def to_dict(self) -> dict[str, Any]:
        value_dump: Any
        if self.value is None:
            value_dump = None
        elif hasattr(self.value, "model_dump"):
            value_dump = self.value.model_dump()
        else:
            value_dump = self.value
        return {
            "ok": self.ok,
            "model_name": self.model_name,
            "value": value_dump,
            "error": None
            if self.error is None
            else {"code": self.error.code, "message": str(self.error)},
            "attempts": [a.to_dict() for a in self.attempts],
        }
