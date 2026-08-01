"""Semantic Kernel-style kernel with plugins and plan invoke (offline)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class KernelFunction:
    name: str
    plugin: str
    handler: Callable[..., str]
    def invoke(self, **kwargs: Any) -> str:
        return self.handler(**kwargs)

@dataclass
class Kernel:
    plugins: dict[str, dict[str, KernelFunction]] = field(default_factory=dict)
    def add_function(self, plugin: str, fn: KernelFunction) -> None:
        self.plugins.setdefault(plugin, {})[fn.name] = fn
    def invoke(self, plugin: str, function: str, **kwargs: Any) -> str:
        return self.plugins[plugin][function].invoke(**kwargs)
    def plan(self, goal: str) -> list[tuple[str, str, dict[str, Any]]]:
        g = goal.lower()
        if "weather" in g:
            return [("weather", "get", {"city": "Berlin"}), ("summary", "wrap", {"text": "$prev"})]
        return [("summary", "wrap", {"text": goal})]
    def run_plan(self, goal: str) -> dict[str, Any]:
        steps = self.plan(goal)
        prev = ""
        trace = []
        for plugin, fn, args in steps:
            a = {k: (prev if v == "$prev" else v) for k, v in args.items()}
            prev = self.invoke(plugin, fn, **a)
            trace.append({"plugin": plugin, "fn": fn, "out": prev})
        return {"ok": True, "framework": "semantic_kernel", "result": prev, "trace": trace}

def demo_kernel() -> Kernel:
    k = Kernel()
    k.add_function("weather", KernelFunction("get", "weather", lambda city="Berlin": f"{city}:18C"))
    k.add_function("summary", KernelFunction("wrap", "summary", lambda text="": f"Summary[{text}]"))
    return k
