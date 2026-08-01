"""LangGraph-style compiled state graph (offline)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

NodeFn = Callable[[dict[str, Any]], dict[str, Any]]

@dataclass
class StateGraph:
    nodes: dict[str, NodeFn] = field(default_factory=dict)
    edges: dict[str, str] = field(default_factory=dict)
    conditionals: dict[str, Callable[[dict[str, Any]], str]] = field(default_factory=dict)
    entry: str = "start"
    def add_node(self, name: str, fn: NodeFn) -> None:
        self.nodes[name] = fn
    def add_edge(self, a: str, b: str) -> None:
        self.edges[a] = b
    def add_conditional(self, a: str, router: Callable[[dict[str, Any]], str]) -> None:
        self.conditionals[a] = router
    def compile(self) -> "CompiledGraph":
        return CompiledGraph(self)

@dataclass
class CompiledGraph:
    g: StateGraph
    def invoke(self, state: dict[str, Any] | None = None, *, max_steps: int = 20) -> dict[str, Any]:
        s = dict(state or {})
        s.setdefault("trace", [])
        node = self.g.entry
        for _ in range(max_steps):
            if node in {"__end__", "end"}:
                break
            if node not in self.g.nodes:
                s["error"] = f"missing:{node}"; break
            out = self.g.nodes[node](s)
            s.update(out)
            s["trace"].append(node)
            if node in self.g.conditionals:
                node = self.g.conditionals[node](s)
            else:
                node = self.g.edges.get(node, "__end__")
        s["ok"] = "error" not in s
        s["framework"] = "langgraph"
        return s

def demo_graph() -> CompiledGraph:
    g = StateGraph(entry="classify")
    g.add_node("classify", lambda s: {"intent": "billing" if "refund" in s.get("text","").lower() else "general"})
    g.add_node("billing", lambda s: {"result": "Refund window 30 days"})
    g.add_node("general", lambda s: {"result": f"Echo: {s.get('text')}"})
    g.add_conditional("classify", lambda s: "billing" if s.get("intent")=="billing" else "general")
    g.add_edge("billing", "end")
    g.add_edge("general", "end")
    g.add_node("end", lambda s: {"done": True})
    return g.compile()
