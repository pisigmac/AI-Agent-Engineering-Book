"""Validate structured tool calls against the registry."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from toolcall.registry import ToolRegistry, ToolRegistryError
from toolcall.specs import AgentTurn


class ToolCallValidationError(ValueError):
    def __init__(self, message: str, *, code: str = "invalid_args") -> None:
        super().__init__(message)
        self.code = code


def parse_agent_turn(data: dict[str, Any]) -> AgentTurn:
    try:
        return AgentTurn.model_validate(data)
    except ValidationError as exc:
        raise ToolCallValidationError(str(exc), code="invalid_turn") from exc


def validate_tool_arguments(
    registry: ToolRegistry, name: str, arguments: dict[str, Any]
) -> Any:
    try:
        spec = registry.get(name)
    except ToolRegistryError as exc:
        raise ToolCallValidationError(str(exc), code="unknown_tool") from exc
    try:
        return spec.args_model.model_validate(arguments or {})
    except ValidationError as exc:
        raise ToolCallValidationError(str(exc), code="invalid_args") from exc
