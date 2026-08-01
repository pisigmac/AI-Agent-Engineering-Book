"""Skill interface, versioning, and composition."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass(frozen=True)
class SkillSpec:
    name: str
    description: str
    version: str = "1.0.0"
    tags: tuple[str, ...] = ()
    input_schema: dict[str, Any] = field(default_factory=dict)

@dataclass
class Skill:
    spec: SkillSpec
    handler: Callable[..., Any]
    def run(self, **kwargs: Any) -> Any:
        return self.handler(**kwargs)
