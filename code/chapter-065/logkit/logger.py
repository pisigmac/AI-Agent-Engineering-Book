"""Structured JSON logging with correlation IDs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import json, time, uuid

@dataclass
class Logger:
    service: str
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    records: list[dict[str, Any]] = field(default_factory=list)
    def bind(self, **fields: Any) -> "Logger":
        child = Logger(self.service, self.correlation_id)
        child.records = self.records
        child._base = {**getattr(self, "_base", {}), **fields}
        return child
    def _emit(self, level: str, msg: str, **fields: Any) -> dict[str, Any]:
        rec = {
            "ts": time.time(),
            "level": level,
            "service": self.service,
            "correlation_id": self.correlation_id,
            "msg": msg,
            **getattr(self, "_base", {}),
            **fields,
        }
        self.records.append(rec)
        return rec
    def info(self, msg: str, **fields: Any) -> dict[str, Any]:
        return self._emit("INFO", msg, **fields)
    def error(self, msg: str, **fields: Any) -> dict[str, Any]:
        return self._emit("ERROR", msg, **fields)
    def dump(self) -> str:
        return chr(10).join(json.dumps(r, sort_keys=True) for r in self.records)
