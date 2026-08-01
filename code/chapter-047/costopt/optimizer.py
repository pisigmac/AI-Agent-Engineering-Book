"""Agent cost optimization: cache, model routing, token budgets."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import hashlib

@dataclass
class CostOptimizer:
    cache: dict[str, str] = field(default_factory=dict)
    spend_usd: float = 0.0
    budget_usd: float = 5.0
    prices: dict[str, float] = field(default_factory=lambda: {"small": 0.01, "large": 0.10})

    def _key(self, prompt: str, model: str) -> str:
        return hashlib.sha256(f"{model}|{prompt}".encode()).hexdigest()

    def choose_model(self, task: str) -> str:
        t = task.lower()
        if any(k in t for k in ("plan", "complex", "multi-hop", "analyze")):
            return "large"
        return "small"

    def complete(self, prompt: str, *, task: str = "") -> dict[str, Any]:
        model = self.choose_model(task or prompt)
        key = self._key(prompt, model)
        if key in self.cache:
            return {"text": self.cache[key], "model": model, "cached": True, "cost_usd": 0.0, "spend_usd": self.spend_usd}
        cost = self.prices[model]
        if self.spend_usd + cost > self.budget_usd:
            return {"error": "budget_exceeded", "spend_usd": self.spend_usd, "model": model}
        self.spend_usd += cost
        text = f"[{model}] response to: {prompt[:80]}"
        self.cache[key] = text
        return {"text": text, "model": model, "cached": False, "cost_usd": cost, "spend_usd": round(self.spend_usd, 4)}
