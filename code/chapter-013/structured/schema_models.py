"""Domain Pydantic models used as structured output contracts."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Intent(str, Enum):
    BILLING = "billing"
    SHIPPING = "shipping"
    REFUND = "refund"
    OTHER = "other"


class RouteDecision(BaseModel):
    """Router output for support ticket classification."""

    model_config = ConfigDict(extra="forbid")

    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    needs_human: bool = False
    rationale: str = Field(min_length=1, max_length=500)

    @field_validator("rationale")
    @classmethod
    def strip_rationale(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("rationale must not be empty")
        return value


class RefundAssessment(BaseModel):
    """Structured refund decision with evidence quotes."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "deny", "escalate"]
    order_id: str | None = None
    reason_code: str = Field(min_length=1, max_length=64)
    evidence: list[str] = Field(default_factory=list)
    needs_human: bool = False
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)

    @field_validator("order_id")
    @classmethod
    def normalize_order_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("evidence")
    @classmethod
    def evidence_strings(cls, value: list[str]) -> list[str]:
        cleaned = [v.strip() for v in value if v and v.strip()]
        return cleaned


def model_to_json_schema(model_type: type[BaseModel]) -> dict[str, Any]:
    return model_type.model_json_schema()
