"""Routed completion with fallbacks — mock providers for offline tests."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Protocol

from modelroute.router import ModelRouter, NoEligibleModelError
from modelroute.types import (
    CompletionResult,
    LatencyClass,
    ModelProfile,
    RouteStrategy,
    TaskRequest,
)


class ModelBackend(Protocol):
    def complete(self, model: ModelProfile, prompt: str) -> tuple[str, int, int, float]:
        """Return (text, input_tokens, output_tokens, latency_ms)."""
        ...


class BackendError(RuntimeError):
    def __init__(self, model_id: str, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.model_id = model_id
        self.retryable = retryable


@dataclass
class MockBackend:
    """Deterministic offline backend with optional forced failures."""

    fail_models: set[str] = field(default_factory=set)
    latency_ms: dict[LatencyClass, float] = field(
        default_factory=lambda: {
            LatencyClass.FAST: 40.0,
            LatencyClass.STANDARD: 120.0,
            LatencyClass.SLOW: 300.0,
        }
    )

    def complete(self, model: ModelProfile, prompt: str) -> tuple[str, int, int, float]:
        if model.model_id in self.fail_models:
            raise BackendError(model.model_id, "simulated provider outage", retryable=True)
        if model.capabilities.embeddings and not model.capabilities.chat:
            raise BackendError(
                model.model_id,
                "embedding model cannot chat-complete",
                retryable=False,
            )
        # Simulate work without sleeping in tests (latency reported, not wall-clock).
        lat = self.latency_ms.get(model.latency, 100.0)
        in_tok = max(1, len(prompt) // 4)
        out_text = f"[{model.model_id}] {prompt[:200]}"
        out_tok = max(1, len(out_text) // 4)
        return out_text, in_tok, out_tok, lat


@dataclass
class RoutedCompleter:
    """Route → try primary → walk fallback chain on retryable failures."""

    router: ModelRouter
    backend: ModelBackend
    default_strategy: RouteStrategy = RouteStrategy.BALANCED

    def complete(
        self,
        task: TaskRequest,
        *,
        strategy: RouteStrategy | None = None,
    ) -> CompletionResult:
        decision = self.router.route(task, strategy=strategy or self.default_strategy)
        attempts: list[dict] = []
        last_err: Exception | None = None
        t0 = time.perf_counter()

        for i, model_id in enumerate(decision.fallback_chain):
            profile = self.router.get(model_id)
            try:
                text, in_tok, out_tok, lat_ms = self.backend.complete(profile, task.prompt)
                cost = profile.estimated_cost_usd(in_tok, out_tok)
                attempts.append(
                    {
                        "model_id": model_id,
                        "ok": True,
                        "latency_ms": lat_ms,
                        "cost_usd": cost,
                    }
                )
                return CompletionResult(
                    text=text,
                    model_id=model_id,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    latency_ms=lat_ms,
                    cost_usd=cost,
                    fallback_used=i > 0,
                    attempts=attempts,
                )
            except BackendError as exc:
                attempts.append(
                    {
                        "model_id": model_id,
                        "ok": False,
                        "error": str(exc),
                        "retryable": exc.retryable,
                    }
                )
                last_err = exc
                if not exc.retryable:
                    break
                continue

        wall = (time.perf_counter() - t0) * 1000
        raise RuntimeError(
            f"all models failed after {len(attempts)} attempt(s) "
            f"in {wall:.1f}ms; last={last_err}; attempts={attempts}"
        )


def build_default_completer(
    *,
    fail_models: set[str] | None = None,
    strategy: RouteStrategy = RouteStrategy.BALANCED,
) -> RoutedCompleter:
    return RoutedCompleter(
        router=ModelRouter(default_strategy=strategy),
        backend=MockBackend(fail_models=fail_models or set()),
        default_strategy=strategy,
    )
