"""Domain model for the canonical AI engineering stack."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LayerId(str, Enum):
    LLM = "llm"
    EMBEDDINGS = "embeddings"
    MEMORY = "memory"
    RETRIEVAL = "retrieval"
    TOOL = "tool"
    SKILL = "skill"
    WORKFLOW = "workflow"
    GRAPH = "graph"
    PLANNER = "planner"
    AGENT = "agent"
    MULTI_AGENT = "multi_agent"
    HARNESS = "harness"
    MCP = "mcp"
    EVAL = "eval"
    OBSERVABILITY = "observability"
    APPLICATION = "application"


@dataclass(frozen=True)
class Layer:
    id: LayerId
    title: str
    purpose: str
    analogy: str
    depends_on: tuple[LayerId, ...] = ()
    produces: tuple[str, ...] = ()
    failure_modes: tuple[str, ...] = ()


@dataclass
class StackRegistry:
    """Canonical AI engineering stack for this book/platform."""

    layers: dict[LayerId, Layer] = field(default_factory=dict)

    def register(self, layer: Layer) -> None:
        if layer.id in self.layers:
            raise ValueError(f"Duplicate layer: {layer.id}")
        self.layers[layer.id] = layer

    def get(self, layer_id: LayerId) -> Layer:
        return self.layers[layer_id]

    def validate_dependencies(self) -> list[str]:
        errors: list[str] = []
        for layer in self.layers.values():
            for dep in layer.depends_on:
                if dep not in self.layers:
                    errors.append(f"{layer.id.value} depends on missing {dep.value}")
        return errors

    def dependents_of(self, layer_id: LayerId) -> list[LayerId]:
        return [lid for lid, layer in self.layers.items() if layer_id in layer.depends_on]

    def summarize(self) -> list[str]:
        lines: list[str] = []
        for layer in self.layers.values():
            deps = ", ".join(d.value for d in layer.depends_on) or "—"
            lines.append(f"{layer.id.value}: {layer.purpose} (depends: {deps})")
        return lines

    def to_mermaid(self) -> str:
        """Emit a flowchart of layer dependencies."""
        lines = ["flowchart BT"]
        for layer in self.layers.values():
            safe = layer.id.value
            label = layer.title.replace('"', "'")
            lines.append(f'  {safe}["{label}"]')
        for layer in self.layers.values():
            for dep in layer.depends_on:
                lines.append(f"  {dep.value} --> {layer.id.value}")
        return "\n".join(lines) + "\n"
