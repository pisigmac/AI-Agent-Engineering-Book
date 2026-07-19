"""Model pricing tables and cost estimation (illustrative rates)."""

from __future__ import annotations

from dataclasses import dataclass

from token_kit.types import TokenUsage


@dataclass(frozen=True)
class ModelPrice:
    model: str
    input_per_mtok: float  # USD per 1M input tokens
    output_per_mtok: float
    context_window: int
    notes: str = ""


class PriceTable:
    """Static illustrative prices — replace with your vendor contract rates."""

    def __init__(self, models: list[ModelPrice] | None = None) -> None:
        default = models or [
            ModelPrice("gpt-4.1", 2.00, 8.00, 1_047_576, "illustrative"),
            ModelPrice("gpt-4.1-mini", 0.40, 1.60, 1_047_576, "illustrative"),
            ModelPrice("gpt-4o", 2.50, 10.00, 128_000, "illustrative"),
            ModelPrice("claude-sonnet-4", 3.00, 15.00, 200_000, "illustrative"),
            ModelPrice("local-7b", 0.0, 0.0, 8192, "self-hosted power only"),
            ModelPrice("mock-llm-8", 0.0, 0.0, 8192, "chapter lab"),
        ]
        self._by_name = {m.model: m for m in default}

    def get(self, model: str) -> ModelPrice:
        if model not in self._by_name:
            known = ", ".join(sorted(self._by_name))
            raise KeyError(f"unknown model '{model}'. known: {known}")
        return self._by_name[model]

    def list_models(self) -> list[str]:
        return sorted(self._by_name)


def estimate_cost(usage: TokenUsage, price: ModelPrice) -> float:
    """Return USD estimate."""
    return (
        usage.input_tokens / 1_000_000.0 * price.input_per_mtok
        + usage.output_tokens / 1_000_000.0 * price.output_per_mtok
    )
