"""Multi-step usage ledger for agent runs."""

from __future__ import annotations

from dataclasses import dataclass, field

from token_kit.pricing import ModelPrice, estimate_cost
from token_kit.types import TokenUsage


@dataclass
class UsageEvent:
    step: str
    usage: TokenUsage
    model: str
    meta: dict[str, object] = field(default_factory=dict)


@dataclass
class UsageLedger:
    events: list[UsageEvent] = field(default_factory=list)

    def add(
        self,
        step: str,
        usage: TokenUsage,
        *,
        model: str,
        **meta: object,
    ) -> None:
        self.events.append(UsageEvent(step=step, usage=usage, model=model, meta=dict(meta)))

    def totals(self) -> TokenUsage:
        inp = sum(e.usage.input_tokens for e in self.events)
        out = sum(e.usage.output_tokens for e in self.events)
        return TokenUsage(input_tokens=inp, output_tokens=out, tokenizer="ledger_sum")

    def estimate_total_cost(self, price: ModelPrice) -> float:
        return sum(estimate_cost(e.usage, price) for e in self.events)

    def to_dict(self, price: ModelPrice | None = None) -> dict[str, object]:
        total = self.totals()
        payload: dict[str, object] = {
            "steps": len(self.events),
            "input_tokens": total.input_tokens,
            "output_tokens": total.output_tokens,
            "total_tokens": total.total_tokens,
            "events": [
                {
                    "step": e.step,
                    "model": e.model,
                    "input_tokens": e.usage.input_tokens,
                    "output_tokens": e.usage.output_tokens,
                    "tokenizer": e.usage.tokenizer,
                    "meta": e.meta,
                }
                for e in self.events
            ],
        }
        if price is not None:
            payload["cost_usd_est"] = round(self.estimate_total_cost(price), 6)
            payload["price_model"] = price.model
        return payload
