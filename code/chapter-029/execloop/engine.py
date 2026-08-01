"""Think-Act-Observe execution engine with retry and terminate."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

DecideFn = Callable[[str, list[dict[str, Any]]], dict[str, Any]]
ActFn = Callable[[dict[str, Any]], dict[str, Any]]

@dataclass
class ExecutionEngine:
    decide: DecideFn
    act: ActFn
    max_steps: int = 8
    max_retries: int = 2

    def run(self, goal: str) -> dict[str, Any]:
        history: list[dict[str, Any]] = []
        retries = 0
        for step in range(self.max_steps):
            thought = self.decide(goal, history)
            history.append({"step": step, "phase": "think", "thought": thought})
            if thought.get("terminate"):
                return {"ok": True, "reason": "terminate", "result": thought.get("result", ""), "history": history}
            action = thought.get("action") or {}
            obs = self.act(action)
            history.append({"step": step, "phase": "act", "action": action, "observe": obs})
            if not obs.get("ok", True):
                retries += 1
                history.append({"step": step, "phase": "retry", "count": retries})
                if retries > self.max_retries:
                    return {"ok": False, "reason": "max_retries", "history": history}
                continue
            retries = 0
            if obs.get("done"):
                return {"ok": True, "reason": "done", "result": obs.get("result", ""), "history": history}
        return {"ok": False, "reason": "max_steps", "history": history}

def default_engine() -> ExecutionEngine:
    state = {"weather_fetched": False}
    def decide(goal: str, history: list[dict[str, Any]]) -> dict[str, Any]:
        if state["weather_fetched"]:
            return {"terminate": True, "result": "Weather task complete", "think": "enough data"}
        if "weather" in goal.lower():
            return {"think": "need weather", "action": {"name": "get_weather", "city": "Berlin"}}
        return {"terminate": True, "result": f"No tools needed for: {goal}", "think": "trivial"}
    def act(action: dict[str, Any]) -> dict[str, Any]:
        if action.get("name") == "get_weather":
            state["weather_fetched"] = True
            return {"ok": True, "done": True, "result": f"{action.get('city')}: 18C"}
        return {"ok": False, "error": "unknown"}
    return ExecutionEngine(decide=decide, act=act)
