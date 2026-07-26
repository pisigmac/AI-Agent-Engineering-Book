"""Illustrative pricing table aligned with chapter-016 style model IDs."""

from __future__ import annotations

from costkit.types import ModelPrice, TokenUsage


def default_prices() -> dict[str, ModelPrice]:
    rows = [
        ModelPrice("openai:gpt-fast", 0.15, 0.60, "illustrative"),
        ModelPrice("openai:gpt-balanced", 2.50, 10.00, "illustrative"),
        ModelPrice("openai:gpt-flagship", 15.00, 60.00, "illustrative"),
        ModelPrice("anthropic:claude-fast", 0.80, 4.00, "illustrative"),
        ModelPrice("anthropic:claude-flagship", 15.00, 75.00, "illustrative"),
        ModelPrice("google:gemini-flash", 0.10, 0.40, "illustrative"),
        ModelPrice("google:gemini-pro", 1.25, 5.00, "illustrative"),
        ModelPrice("mistral:small", 0.20, 0.60, "illustrative"),
        ModelPrice("mistral:large", 2.00, 6.00, "illustrative"),
        ModelPrice("meta:llama-local-8b", 0.0, 0.0, "self-hosted"),
        ModelPrice("meta:llama-local-70b", 0.0, 0.0, "self-hosted"),
        ModelPrice("local:embed-mini", 0.0, 0.0, "embeddings"),
        ModelPrice("mock-default", 1.00, 3.00, "tests"),
    ]
    return {p.model_id: p for p in rows}


class PriceBook:
    def __init__(self, prices: dict[str, ModelPrice] | None = None) -> None:
        self._prices = dict(prices) if prices is not None else default_prices()

    def get(self, model_id: str) -> ModelPrice:
        if model_id in self._prices:
            return self._prices[model_id]
        # Unknown model: conservative mid-tier so missing prices are visible
        return ModelPrice(model_id, 5.00, 15.00, "unknown-model-fallback")

    def cost(self, model_id: str, usage: TokenUsage) -> float:
        return self.get(model_id).cost_usd(usage)

    def list_models(self) -> list[str]:
        return sorted(self._prices)
