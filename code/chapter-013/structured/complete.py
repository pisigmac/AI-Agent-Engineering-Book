"""Structured completion with extract → validate → bounded repair."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from structured.extract import extract_json_object
from structured.types import (
    AttemptRecord,
    StructureExhaustedError,
    StructureParseError,
    StructureValidationError,
    StructuredOutputError,
    StructuredResult,
)
from structured.validate import validate_model

T = TypeVar("T", bound=BaseModel)

GenerateFn = Callable[[list[dict[str, str]]], str]


class StructuredCompleter:
    def __init__(
        self,
        generate: GenerateFn,
        *,
        max_repairs: int = 2,
        model_name: str = "structured-completer",
    ) -> None:
        if max_repairs < 0:
            raise ValueError("max_repairs must be >= 0")
        self.generate = generate
        self.max_repairs = max_repairs
        self.model_name = model_name

    def complete(
        self,
        messages: list[dict[str, str]],
        model_type: type[T],
        *,
        max_repairs: int | None = None,
    ) -> StructuredResult:
        repairs = self.max_repairs if max_repairs is None else max_repairs
        attempts: list[AttemptRecord] = []
        conversation = [dict(m) for m in messages]
        schema_hint = json.dumps(model_type.model_json_schema(), indent=2)

        # Ensure the contract is visible on first try if not already present.
        if not any("json" in m.get("content", "").lower() for m in conversation):
            conversation.append(
                {
                    "role": "system",
                    "content": (
                        f"Return ONLY a JSON object matching this schema:\n{schema_hint}"
                    ),
                }
            )

        total_tries = repairs + 1
        last_error: StructuredOutputError | None = None

        for i in range(total_tries):
            raw = self.generate(conversation)
            try:
                parsed = extract_json_object(raw)
                value = validate_model(model_type, parsed)
                attempts.append(
                    AttemptRecord(
                        index=i,
                        raw_text=raw,
                        ok=True,
                        parsed=parsed,
                    )
                )
                return StructuredResult(
                    value=value,
                    error=None,
                    attempts=attempts,
                    model_name=self.model_name,
                )
            except (StructureParseError, StructureValidationError) as exc:
                last_error = exc
                attempts.append(
                    AttemptRecord(
                        index=i,
                        raw_text=raw,
                        ok=False,
                        error_code=exc.code,
                        error_message=str(exc),
                    )
                )
                if i >= total_tries - 1:
                    break
                conversation.append({"role": "assistant", "content": raw})
                conversation.append(
                    {
                        "role": "user",
                        "content": _repair_message(exc, model_type),
                    }
                )

        err = StructureExhaustedError(
            f"failed after {total_tries} attempt(s): {last_error}"
        )
        return StructuredResult(
            value=None,
            error=err,
            attempts=attempts,
            model_name=self.model_name,
        )


def _repair_message(exc: StructuredOutputError, model_type: type[BaseModel]) -> str:
    schema = json.dumps(model_type.model_json_schema(), indent=2)
    details = str(exc)
    if isinstance(exc, StructureValidationError) and exc.errors:
        details = json.dumps(exc.errors, indent=2)
    return (
        "Your previous answer failed structural validation.\n"
        f"Error ({exc.code}):\n{details}\n\n"
        "Return ONLY a corrected JSON object (no markdown, no prose) "
        f"matching this schema:\n{schema}"
    )
