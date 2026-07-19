"""Shared request/result types for async HTTP utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class RequestSpec:
    method: str
    url: str
    headers: Mapping[str, str] = field(default_factory=dict)
    json_body: Any | None = None
    params: Mapping[str, str] | None = None
    timeout_s: float = 30.0
    idempotent: bool = False


@dataclass(frozen=True)
class ResponseEnvelope:
    status_code: int
    headers: Mapping[str, str]
    body_text: str
    request_id: str
    elapsed_s: float

    def json(self) -> Any:
        import json

        return json.loads(self.body_text)


@dataclass(frozen=True)
class ItemResult:
    key: str
    ok: bool
    value: Any = None
    error: str | None = None
    status_code: int | None = None
