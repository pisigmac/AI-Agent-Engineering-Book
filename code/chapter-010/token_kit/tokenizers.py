"""Token counters: approximate cl100k-style, char heuristic, optional tiktoken."""

from __future__ import annotations

import math
import re
from typing import Protocol

from token_kit.types import ChatMessage

# Portable approximation of BPE-ish splitting (std re has no \p{L}/\p{N}).
_PORTABLE_PATTERN = re.compile(
    r"""'(?:[sdmt]|ll|ve|re)|[^\r\n\w]?[a-zA-Z]+|\d{1,3}| ?[^\s\w]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+""",
    re.IGNORECASE,
)


class TokenCounter(Protocol):
    name: str

    def count_text(self, text: str) -> int: ...

    def count_messages(self, messages: list[ChatMessage]) -> int: ...


class CharHeuristicCounter:
    """Rough fallback: ~4 chars/token. Not for billing accuracy."""

    name = "char_heuristic_v1"

    def count_text(self, text: str) -> int:
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 4))

    def count_messages(self, messages: list[ChatMessage]) -> int:
        # Chat formatting overhead ≈ 4 tokens/message + role priming (OpenAI-ish rule of thumb)
        total = 3  # reply priming
        for msg in messages:
            total += 4
            total += self.count_text(msg.content)
            if msg.name:
                total += self.count_text(msg.name)
        return total


class ApproxCl100kCounter:
    """Dependency-free approximation using a BPE-like regex split.

    Not bit-identical to tiktoken; good enough for budgets and tests.
    """

    name = "approx_cl100k_v1"

    def count_text(self, text: str) -> int:
        if not text:
            return 0
        pieces = _PORTABLE_PATTERN.findall(text)
        if not pieces:
            return max(1, math.ceil(len(text) / 4))
        # Subword inflation for long alphanumerics
        count = 0
        for p in pieces:
            if p.isdigit():
                count += max(1, math.ceil(len(p) / 3))
            elif len(p) > 12 and p.isidentifier():
                count += max(1, math.ceil(len(p) / 4))
            else:
                count += 1
        return count

    def count_messages(self, messages: list[ChatMessage]) -> int:
        total = 3
        for msg in messages:
            total += 4
            total += self.count_text(msg.role.value)
            total += self.count_text(msg.content)
            if msg.name:
                total += self.count_text(msg.name) + 1
        return total


class TiktokenCounter:
    """Optional exact-ish OpenAI counting when tiktoken is installed."""

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        try:
            import tiktoken
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "tiktoken is not installed. pip install tiktoken or use ApproxCl100kCounter"
            ) from exc
        self.name = f"tiktoken:{encoding_name}"
        self._enc = tiktoken.get_encoding(encoding_name)

    def count_text(self, text: str) -> int:
        return len(self._enc.encode(text))

    def count_messages(self, messages: list[ChatMessage]) -> int:
        # Mirrors OpenAI chat estimation structure at a high level
        total = 3
        for msg in messages:
            total += 4
            total += self.count_text(msg.content)
            total += self.count_text(msg.role.value)
            if msg.name:
                total += self.count_text(msg.name) + 1
        return total


def get_default_counter(*, prefer_tiktoken: bool = False) -> TokenCounter:
    if prefer_tiktoken:
        try:
            return TiktokenCounter()
        except RuntimeError:
            pass
    return ApproxCl100kCounter()
