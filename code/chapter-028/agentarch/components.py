"""Default implementations of agent architecture components."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class WorkingMemory:
    items: list[tuple[str, str]] = field(default_factory=list)
    def add(self, role: str, content: str) -> None:
        self.items.append((role, content))
    def context(self) -> str:
        return "\n".join(f"{r}: {c}" for r, c in self.items[-12:])

@dataclass
class SimplePlanner:
    def plan(self, goal: str) -> list[str]:
        g = goal.lower()
        steps = ["understand_goal"]
        if any(k in g for k in ("weather", "search", "lookup", "refund", "policy")):
            steps.append("use_tools")
        steps.append("compose_answer")
        steps.append("stop")
        return steps

@dataclass
class ToolBus:
    handlers: dict = field(default_factory=dict)
    def register(self, name: str, fn) -> None:
        self.handlers[name] = fn
    def call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name not in self.handlers:
            return {"ok": False, "error": f"unknown_tool:{name}"}
        try:
            return {"ok": True, "result": self.handlers[name](**args)}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)}

@dataclass
class Skill:
    name: str
    description: str
    run_fn: Any
    def run(self, input: str) -> str:
        return str(self.run_fn(input))

@dataclass
class StepExecutor:
    def execute(self, step: str, tools: ToolBus, goal: str, memory: WorkingMemory) -> str:
        if step == "understand_goal":
            memory.add("system", f"goal={goal}")
            return "understood"
        if step == "use_tools":
            g = goal.lower()
            if "weather" in g:
                out = tools.call("weather", {"city": "Berlin"})
            elif "refund" in g or "policy" in g:
                out = tools.call("policy", {"topic": "refund"})
            else:
                out = tools.call("echo", {"text": goal})
            memory.add("tool", str(out))
            return str(out)
        if step == "compose_answer":
            ans = f"Answer based on memory:\n{memory.context()}"
            memory.add("assistant", ans)
            return ans
        return "stop"
