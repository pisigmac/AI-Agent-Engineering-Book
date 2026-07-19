"""Application use cases (orchestration over ports)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from platform_core.domain import CompletionRequest, RunRecord
from platform_core.ports import Clock, IdFactory, LLMPort, RunRepository


@dataclass
class CompleteText:
    """Complete a prompt via LLMPort and persist a run record."""

    llm: LLMPort
    runs: RunRepository
    clock: Clock
    ids: IdFactory
    logger: logging.Logger
    default_model: str = "demo"

    def __call__(self, prompt: str, *, model: str | None = None) -> RunRecord:
        request = CompletionRequest(prompt=prompt, model=model or self.default_model)
        self.logger.info("complete_start model=%s", request.model)
        response = self.llm.complete(request)
        record = RunRecord(
            run_id=self.ids.new_id(),
            goal=prompt,
            output=response.text,
            created_at=self.clock.time(),
            provider=response.model,
        )
        self.runs.save(record)
        self.logger.info(
            "complete_done run_id=%s tokens=%s",
            record.run_id,
            response.usage_tokens,
        )
        return record
