"""JSON encode/decode with explicit errors."""

from __future__ import annotations

import json
from typing import Any


class JsonError(ValueError):
    pass


def dumps(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=str)
    except (TypeError, ValueError) as exc:
        raise JsonError(f"json encode failed: {exc}") from exc


def loads(text: str) -> Any:
    if text is None or str(text).strip() == "":
        raise JsonError("empty json body")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise JsonError(f"json decode failed: {exc}") from exc
