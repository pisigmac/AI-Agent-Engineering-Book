"""Helpers for SSE and NDJSON-style streams."""

from __future__ import annotations

from typing import Any, Iterable, Iterator

from json_codec import JsonError, loads


def iter_sse_lines(lines: Iterable[str]) -> Iterator[str]:
    """Yield data payloads from SSE-style lines."""
    for raw in lines:
        line = raw.strip("\r")
        if not line or line.startswith(":"):
            continue
        if line.startswith("data:"):
            yield line[5:].lstrip()


def iter_ndjson(lines: Iterable[str]) -> Iterator[Any]:
    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        try:
            yield loads(text)
        except JsonError:
            continue
