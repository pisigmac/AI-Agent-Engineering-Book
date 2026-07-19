"""Ports (interfaces) the application core depends on."""

from __future__ import annotations

from typing import Protocol

from platform_core.domain import CompletionRequest, CompletionResponse, RunRecord


class LLMPort(Protocol):
    def complete(self, request: CompletionRequest) -> CompletionResponse: ...


class RunRepository(Protocol):
    def save(self, run: RunRecord) -> None: ...

    def get(self, run_id: str) -> RunRecord | None: ...


class Clock(Protocol):
    def time(self) -> float: ...


class IdFactory(Protocol):
    def new_id(self) -> str: ...
