"""Provider-abstracted LLM client with retries and streaming."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterator, Protocol
import time

class Provider(Protocol):
    name: str
    def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]: ...
    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]: ...

@dataclass
class MockProvider:
    name: str = "mock"
    fail_times: int = 0
    _fails: int = 0
    def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        if self._fails < self.fail_times:
            self._fails += 1
            raise TimeoutError("transient")
        text = messages[-1]["content"] if messages else ""
        return {"text": f"[{self.name}] {text[:120]}", "usage": {"in": 10, "out": 20}, "model": kwargs.get("model", "mock-1")}
    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]:
        full = self.complete(messages, **kwargs)["text"]
        for i in range(0, len(full), 8):
            yield full[i:i+8]

@dataclass
class LLMClient:
    provider: Provider
    max_retries: int = 3
    backoff_s: float = 0.0
    def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        last: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                out = self.provider.complete(messages, **kwargs)
                out["attempts"] = attempt
                return out
            except Exception as e:  # noqa: BLE001
                last = e
                if attempt < self.max_retries and self.backoff_s:
                    time.sleep(self.backoff_s)
        raise RuntimeError(f"complete failed after retries: {last}")
    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> list[str]:
        return list(self.provider.stream(messages, **kwargs))
