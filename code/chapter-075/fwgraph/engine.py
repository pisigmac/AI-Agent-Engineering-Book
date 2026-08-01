"""Graph engine: nodes, edges, shared state."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

NodeFn = Callable[[dict[str, Any]], dict[str, Any]]

@dataclass
class GraphEngine:
    nodes: dict[str, NodeFn] = field(default_factory=dict)
    edges: dict[str, str] = field(default_factory=dict)
    start: str = "start"
    def add_node(self, name: str, fn: NodeFn) -> None:
        self.nodes[name] = fn
    def add_edge(self, a: str, b: str) -> None:
        self.edges[a] = b
    def run(self, state: dict[str, Any] | None = None, *, max_steps: int = 20) -> dict[str, Any]:
        s = dict(state or {}); s.setdefault("path", []); node = self.start
        for _ in range(max_steps):
            if node in {"end", "__end__"}: break
            s.update(self.nodes[node](s)); s["path"].append(node)
            node = self.edges.get(node, "end")
        s["ok"] = True
        return s
