"""Deterministic LLM adapter for local demos and tests."""

from __future__ import annotations

from platform_core.domain import CompletionRequest, CompletionResponse
from platform_core.errors import ValidationError


class MockLLMAdapter:
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        if not request.prompt.strip():
            raise ValidationError("prompt must not be empty")
        text = f"[{request.model}] echo: {request.prompt.strip()}"
        return CompletionResponse(
            text=text,
            model=request.model,
            usage_tokens=max(1, len(request.prompt.split())),
        )
