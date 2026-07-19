"""HTTP client value objects."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class AuthConfig:
    """How to attach credentials. Load secret values from the environment at call sites."""

    kind: str = "none"  # none | bearer | header | basic
    token: str | None = None
    header_name: str = "Authorization"
    username: str | None = None
    password: str | None = None

    def headers(self) -> dict[str, str]:
        if self.kind == "none":
            return {}
        if self.kind == "bearer":
            if not self.token:
                raise ValueError("bearer auth requires token")
            return {"Authorization": f"Bearer {self.token}"}
        if self.kind == "header":
            if not self.token:
                raise ValueError("header auth requires token")
            return {self.header_name: self.token}
        if self.kind == "basic":
            if self.username is None:
                raise ValueError("basic auth requires username")
            raw = f"{self.username}:{self.password or ''}".encode()
            return {"Authorization": "Basic " + base64.b64encode(raw).decode()}
        raise ValueError(f"unknown auth kind: {self.kind}")


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
        from json_codec import loads

        return loads(self.body_text)
