"""Agent graph execution: DAG nodes, routing, fan-out/in, checkpoints."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

NodeFn = Callable[[dict[str, Any]], dict[str, Any]]

@dataclass
class Node:
    name: str
    fn: NodeFn
    nexts: list[str] = field(default_factory=list)  # static edges
    router: Callable[[dict[str, Any]], list[str]] | None = None

@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    start: str = "start"
    def add(self, node: Node) -> None:
        self.nodes[node.name] = node
    def run(self, payload: dict[str, Any] | None = None, *, max_nodes: int = 32) -> dict[str, Any]:
        state = dict(payload or {})
        state.setdefault("trace", [])
        state.setdefault("checkpoints", [])
        current = [self.start]
        seen = 0
        while current and seen < max_nodes:
            name = current.pop(0)
            if name not in self.nodes:
                state["trace"].append({"error": f"missing_node:{name}"})
                break
            node = self.nodes[name]
            out = node.fn(state)
            state.update(out)
            state["trace"].append({"node": name, "out_keys": list(out.keys())})
            state["checkpoints"].append({"node": name, "snapshot": {k: state.get(k) for k in ("result", "branch")}})
            seen += 1
            if node.router:
                current.extend(node.router(state))
            else:
                current.extend(node.nexts)
        state["ok"] = "error" not in str(state.get("trace", []))
        return state

def research_graph() -> Graph:
    g = Graph(start="plan")
    g.add(Node("plan", lambda s: {"plan": ["search", "write"], "branch": "search"}, nexts=["search"]))
    g.add(Node("search", lambda s: {"notes": f"notes for {s.get('goal','topic')}"}, nexts=["write"]))
    g.add(Node("write", lambda s: {"result": f"Report: {s.get('notes','')}"}, nexts=["end"]))
    g.add(Node("end", lambda s: {"done": True}, nexts=[]))
    return g
