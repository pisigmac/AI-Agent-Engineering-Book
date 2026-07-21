"""Validate dictionaries into Pydantic models with stable errors."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from structured.types import StructureValidationError

T = TypeVar("T", bound=BaseModel)


def validate_model(model_type: type[T], data: dict[str, Any]) -> T:
    try:
        return model_type.model_validate(data)
    except ValidationError as exc:
        errors = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", ()))
            errors.append(
                {
                    "loc": loc,
                    "msg": err.get("msg"),
                    "type": err.get("type"),
                }
            )
        summary = "; ".join(f"{e['loc']}: {e['msg']}" for e in errors) or str(exc)
        raise StructureValidationError(summary, errors=errors) from exc
