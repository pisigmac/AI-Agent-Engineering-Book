"""Exact-match response cache with TTL and cost-savings accounting."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float
    hits: int = 0
    model_id: str = ""
    saved_cost_usd: float = 0.0


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    bypasses: int = 0
    saved_cost_usd: float = 0.0
    entries: int = 0

    @property
    def hit_rate(self) -> float:
        t = self.hits + self.misses
        return self.hits / t if t else 0.0

    def to_dict(self) -> dict[str, float | int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "bypasses": self.bypasses,
            "hit_rate": round(self.hit_rate, 4),
            "saved_cost_usd": round(self.saved_cost_usd, 8),
            "entries": self.entries,
        }


def make_cache_key(
    *,
    model_id: str,
    prompt: str,
    system: str = "",
    temperature: float = 0.0,
    extra: str = "",
) -> str:
    raw = f"{model_id}|t={temperature}|sys={system}|p={prompt}|x={extra}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ResponseCache:
    """In-process exact cache. Production: Redis with the same key contract."""

    def __init__(self, *, ttl_s: float = 3600.0, max_entries: int = 10_000) -> None:
        if ttl_s <= 0:
            raise ValueError("ttl_s must be positive")
        if max_entries < 1:
            raise ValueError("max_entries must be >= 1")
        self.ttl_s = ttl_s
        self.max_entries = max_entries
        self._store: dict[str, CacheEntry] = {}
        self.stats = CacheStats()
        self._clock: Callable[[], float] = time.time

    def clear(self) -> None:
        self._store.clear()
        self.stats = CacheStats()

    def _evict_expired(self, now: float) -> None:
        dead = [k for k, e in self._store.items() if now - e.created_at > self.ttl_s]
        for k in dead:
            del self._store[k]

    def _evict_overflow(self) -> None:
        while len(self._store) > self.max_entries:
            # Drop oldest
            oldest = min(self._store.items(), key=lambda kv: kv[1].created_at)
            del self._store[oldest[0]]

    def get(self, key: str) -> Any | None:
        now = self._clock()
        self._evict_expired(now)
        entry = self._store.get(key)
        if entry is None:
            self.stats.misses += 1
            self.stats.entries = len(self._store)
            return None
        entry.hits += 1
        self.stats.hits += 1
        self.stats.saved_cost_usd += entry.saved_cost_usd
        self.stats.entries = len(self._store)
        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        *,
        model_id: str = "",
        unit_cost_usd: float = 0.0,
    ) -> None:
        now = self._clock()
        self._evict_expired(now)
        self._store[key] = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            model_id=model_id,
            saved_cost_usd=unit_cost_usd,
        )
        self._evict_overflow()
        self.stats.entries = len(self._store)

    def bypass(self) -> None:
        self.stats.bypasses += 1
