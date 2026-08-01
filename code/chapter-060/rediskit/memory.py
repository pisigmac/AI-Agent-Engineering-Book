"""Redis-like in-memory store: cache, rate limit, sessions."""
from __future__ import annotations
from dataclasses import dataclass, field
from time import time
from typing import Any

@dataclass
class RedisLite:
    kv: dict[str, tuple[Any, float | None]] = field(default_factory=dict)
    lists: dict[str, list[Any]] = field(default_factory=dict)
    def set(self, key: str, value: Any, *, ex: float | None = None) -> None:
        exp = time() + ex if ex else None
        self.kv[key] = (value, exp)
    def get(self, key: str) -> Any | None:
        item = self.kv.get(key)
        if not item: return None
        val, exp = item
        if exp is not None and time() > exp:
            self.kv.pop(key, None); return None
        return val
    def incr(self, key: str) -> int:
        cur = int(self.get(key) or 0) + 1
        self.set(key, cur)
        return cur
    def allow_rate(self, key: str, *, limit: int, window_s: float) -> bool:
        # simple fixed window counter
        bucket = f"rl:{key}:{int(time() // window_s)}"
        n = self.incr(bucket)
        # expire bucket roughly
        self.set(bucket, n, ex=window_s)
        return n <= limit
    def session_set(self, sid: str, data: dict[str, Any], *, ttl: float = 3600) -> None:
        self.set(f"sess:{sid}", data, ex=ttl)
    def session_get(self, sid: str) -> dict[str, Any] | None:
        val = self.get(f"sess:{sid}")
        return val if isinstance(val, dict) else None
