"""Tool registration and schema export."""

from __future__ import annotations

from typing import Any

from toolcall.specs import ToolSpec


class ToolRegistryError(KeyError):
    pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if not spec.name or not spec.name.replace("_", "").isalnum():
            raise ValueError(f"invalid tool name: {spec.name!r}")
        if spec.name in self._tools:
            raise ValueError(f"duplicate tool: {spec.name}")
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolRegistryError(f"unknown tool: {name}") from exc

    def list(self) -> list[str]:
        return sorted(self._tools)

    def export_schemas(self) -> list[dict[str, Any]]:
        return [self._tools[n].json_schema() for n in self.list()]

    def descriptions_for_prompt(self) -> str:
        lines = ["Available tools:"]
        for name in self.list():
            spec = self._tools[name]
            lines.append(f"- {name}: {spec.description}")
        return "\n".join(lines)
