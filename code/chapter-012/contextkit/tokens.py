"""Token estimation for assembly decisions."""

from __future__ import annotations

import math
import re
from typing import Protocol

_WORDISH = re.compile(
    r"""'(?:[sdmt]|ll|ve|re)|[^\r\n\w]?[a-zA-Z]+|\d{1,3}| ?[^\s\w]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+""",
    re.IGNORECASE,
)


class TokenEstimator(Protocol):
    name: str

    def count_text(self, text: str) -> int: ...

    def count_messages(self, messages: list[dict[str, str]]) -> int: ...


class ApproxTokenEstimator:
    """Dependency-free estimator suitable for unit tests and preflight gates."""

    name = "approx_contextkit_v1"

    def count_text(self, text: str) -> int:
        if not text:
            return 0
        pieces = _WORDISH.findall(text)
        if not pieces:
            return max(1, math.ceil(len(text) / 4))
        total = 0
        for piece in pieces:
            if piece.isdigit():
                total += max(1, math.ceil(len(piece) / 3))
            elif len(piece) > 12:
                total += max(1, math.ceil(len(piece) / 4))
            else:
                total += 1
        return total

    def count_messages(self, messages: list[dict[str, str]]) -> int:
        # Chat framing overhead similar to common OpenAI-style heuristics.
        total = 3
        for message in messages:
            total += 4
            total += self.count_text(message.get("role", ""))
            total += self.count_text(message.get("content", ""))
        return total
