"""Illustrative model catalog — pin real IDs and prices in your environment."""

from __future__ import annotations

from modelroute.types import (
    LatencyClass,
    ModelCapabilities,
    ModelProfile,
    Provider,
    QualityTier,
)


def default_catalog() -> list[ModelProfile]:
    """Representative 2026-style catalog for routing demos.

    Prices and names are **teaching fixtures**, not live vendor quotes.
    Production: load from config / feature flags / pricing service.
    """
    return [
        ModelProfile(
            model_id="openai:gpt-fast",
            display_name="GPT Fast (small)",
            provider=Provider.OPENAI,
            quality=QualityTier.SMALL,
            latency=LatencyClass.FAST,
            context_window=128_000,
            input_cost_per_1m=0.15,
            output_cost_per_1m=0.60,
            capabilities=ModelCapabilities(
                chat=True, tools=True, json_mode=True, code=True
            ),
            tags=("default-cheap", "classify"),
            notes="High-volume classification and simple chat.",
        ),
        ModelProfile(
            model_id="openai:gpt-balanced",
            display_name="GPT Balanced",
            provider=Provider.OPENAI,
            quality=QualityTier.LARGE,
            latency=LatencyClass.STANDARD,
            context_window=128_000,
            input_cost_per_1m=2.50,
            output_cost_per_1m=10.00,
            capabilities=ModelCapabilities(
                chat=True, tools=True, json_mode=True, code=True, vision=True
            ),
            tags=("general", "tools"),
            notes="Default general assistant when quality matters.",
        ),
        ModelProfile(
            model_id="openai:gpt-flagship",
            display_name="GPT Flagship",
            provider=Provider.OPENAI,
            quality=QualityTier.FLAGSHIP,
            latency=LatencyClass.SLOW,
            context_window=200_000,
            input_cost_per_1m=15.00,
            output_cost_per_1m=60.00,
            capabilities=ModelCapabilities(
                chat=True,
                tools=True,
                json_mode=True,
                code=True,
                vision=True,
                long_context=True,
            ),
            tags=("hard-reasoning", "escalation"),
            notes="Expensive escalation for hard reasoning.",
        ),
        ModelProfile(
            model_id="anthropic:claude-fast",
            display_name="Claude Fast",
            provider=Provider.ANTHROPIC,
            quality=QualityTier.MEDIUM,
            latency=LatencyClass.FAST,
            context_window=200_000,
            input_cost_per_1m=0.80,
            output_cost_per_1m=4.00,
            capabilities=ModelCapabilities(
                chat=True, tools=True, json_mode=True, code=True, long_context=True
            ),
            tags=("docs", "summarize"),
        ),
        ModelProfile(
            model_id="anthropic:claude-flagship",
            display_name="Claude Flagship",
            provider=Provider.ANTHROPIC,
            quality=QualityTier.FLAGSHIP,
            latency=LatencyClass.STANDARD,
            context_window=200_000,
            input_cost_per_1m=15.00,
            output_cost_per_1m=75.00,
            capabilities=ModelCapabilities(
                chat=True,
                tools=True,
                json_mode=True,
                code=True,
                vision=True,
                long_context=True,
            ),
            tags=("writing", "careful-tools"),
        ),
        ModelProfile(
            model_id="google:gemini-flash",
            display_name="Gemini Flash",
            provider=Provider.GOOGLE,
            quality=QualityTier.MEDIUM,
            latency=LatencyClass.FAST,
            context_window=1_000_000,
            input_cost_per_1m=0.10,
            output_cost_per_1m=0.40,
            capabilities=ModelCapabilities(
                chat=True,
                tools=True,
                json_mode=True,
                vision=True,
                long_context=True,
                code=True,
            ),
            tags=("long-context", "cheap-multimodal"),
        ),
        ModelProfile(
            model_id="google:gemini-pro",
            display_name="Gemini Pro",
            provider=Provider.GOOGLE,
            quality=QualityTier.LARGE,
            latency=LatencyClass.STANDARD,
            context_window=1_000_000,
            input_cost_per_1m=1.25,
            output_cost_per_1m=5.00,
            capabilities=ModelCapabilities(
                chat=True,
                tools=True,
                json_mode=True,
                vision=True,
                long_context=True,
                code=True,
            ),
            tags=("multimodal",),
        ),
        ModelProfile(
            model_id="meta:llama-local-8b",
            display_name="Llama 8B (local)",
            provider=Provider.META,
            quality=QualityTier.SMALL,
            latency=LatencyClass.FAST,
            context_window=8_192,
            input_cost_per_1m=0.0,
            output_cost_per_1m=0.0,
            capabilities=ModelCapabilities(
                chat=True, code=True, open_weights=True, json_mode=True
            ),
            tags=("private", "on-prem", "open-weights"),
            notes="Zero marginal API cost; you pay infra. Weak tools by default.",
        ),
        ModelProfile(
            model_id="meta:llama-local-70b",
            display_name="Llama 70B (local)",
            provider=Provider.META,
            quality=QualityTier.LARGE,
            latency=LatencyClass.SLOW,
            context_window=32_768,
            input_cost_per_1m=0.0,
            output_cost_per_1m=0.0,
            capabilities=ModelCapabilities(
                chat=True, code=True, open_weights=True, json_mode=True, tools=True
            ),
            tags=("private", "on-prem", "open-weights"),
        ),
        ModelProfile(
            model_id="mistral:small",
            display_name="Mistral Small",
            provider=Provider.MISTRAL,
            quality=QualityTier.MEDIUM,
            latency=LatencyClass.FAST,
            context_window=32_768,
            input_cost_per_1m=0.20,
            output_cost_per_1m=0.60,
            capabilities=ModelCapabilities(
                chat=True, tools=True, json_mode=True, code=True
            ),
            tags=("eu", "efficient"),
        ),
        ModelProfile(
            model_id="mistral:large",
            display_name="Mistral Large",
            provider=Provider.MISTRAL,
            quality=QualityTier.LARGE,
            latency=LatencyClass.STANDARD,
            context_window=128_000,
            input_cost_per_1m=2.00,
            output_cost_per_1m=6.00,
            capabilities=ModelCapabilities(
                chat=True, tools=True, json_mode=True, code=True
            ),
            tags=("eu", "general"),
        ),
        ModelProfile(
            model_id="local:embed-mini",
            display_name="Local Embed Mini",
            provider=Provider.LOCAL,
            quality=QualityTier.SMALL,
            latency=LatencyClass.FAST,
            context_window=512,
            input_cost_per_1m=0.0,
            output_cost_per_1m=0.0,
            capabilities=ModelCapabilities(
                chat=False, embeddings=True, open_weights=True
            ),
            tags=("embeddings",),
            notes="Embedding-only model; not for chat completion.",
        ),
    ]


def catalog_by_id(profiles: list[ModelProfile] | None = None) -> dict[str, ModelProfile]:
    profiles = profiles if profiles is not None else default_catalog()
    return {p.model_id: p for p in profiles}
