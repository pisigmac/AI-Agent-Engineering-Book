"""Extract a JSON object from messy LLM text."""

from __future__ import annotations

import json
import re
from typing import Any

from structured.types import StructureParseError

_FENCE = re.compile(r"```(?:json|JSON)?\s*([\s\S]*?)```", re.MULTILINE)


def extract_json_object(text: str) -> dict[str, Any]:
    """Pull the first JSON object from model output.

    Accepts pure JSON, fenced blocks, or prose-wrapped objects.
    """
    if text is None or not str(text).strip():
        raise StructureParseError("empty model output")

    candidates: list[str] = []
    for match in _FENCE.finditer(text):
        candidates.append(match.group(1).strip())
    stripped = text.strip()
    candidates.append(stripped)

    # Balanced-brace scan for embedded objects
    candidates.extend(_balanced_objects(text))

    last_err: Exception | None = None
    for candidate in candidates:
        if not candidate:
            continue
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_err = exc
            # try minor cleanup: trailing commas
            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as exc2:
                last_err = exc2
                continue
        if isinstance(data, dict):
            return data
        last_err = StructureParseError(f"JSON root must be object, got {type(data).__name__}")

    raise StructureParseError(
        f"could not extract JSON object: {last_err}"
    ) from last_err


def _balanced_objects(text: str) -> list[str]:
    objs: list[str] = []
    start = None
    depth = 0
    in_str = False
    escape = False
    for i, ch in enumerate(text):
        if start is None:
            if ch == "{":
                start = i
                depth = 1
                in_str = False
                escape = False
            continue
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                objs.append(text[start : i + 1])
                start = None
    return objs
