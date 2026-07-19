"""Composition root: wire settings → adapters → services."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from platform_core.adapters.memory_repo import InMemoryRunRepository
from platform_core.adapters.mock_llm import MockLLMAdapter
from platform_core.clock import SystemClock
from platform_core.config import Settings
from platform_core.errors import ConfigurationError
from platform_core.ports import IdFactory, LLMPort, RunRepository
from platform_core.services import CompleteText


class UuidFactory:
    def new_id(self) -> str:
        return str(uuid.uuid4())


class SequenceIdFactory:
    """Deterministic IDs for tests."""

    def __init__(self, start: int = 1) -> None:
        self._n = start

    def new_id(self) -> str:
        value = f"run-{self._n:04d}"
        self._n += 1
        return value


@dataclass
class Container:
    settings: Settings
    complete_text: CompleteText
    runs: RunRepository
    llm: LLMPort


def build_llm(settings: Settings) -> LLMPort:
    if settings.provider == "mock":
        return MockLLMAdapter()
    # Future: return OpenAIAdapter(HttpClient(...), settings)
    raise ConfigurationError(
        f"unsupported LLM provider '{settings.provider}'. "
        "Chapter 8+ will wire real adapters; use LLM_PROVIDER=mock for now."
    )


def build_container(
    settings: Settings | None = None,
    *,
    llm: LLMPort | None = None,
    runs: RunRepository | None = None,
    ids: IdFactory | None = None,
    logger: logging.Logger | None = None,
) -> Container:
    settings = settings or Settings.from_env()
    llm = llm or build_llm(settings)
    runs = runs or InMemoryRunRepository()
    ids = ids or UuidFactory()
    logger = logger or logging.getLogger("platform")
    service = CompleteText(
        llm=llm,
        runs=runs,
        clock=SystemClock(),
        ids=ids,
        logger=logger,
        default_model=settings.default_model,
    )
    return Container(settings=settings, complete_text=service, runs=runs, llm=llm)
