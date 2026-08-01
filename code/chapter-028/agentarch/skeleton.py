"""Agent skeleton wiring planner, memory, executor, tools, skills, harness."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from agentarch.components import SimplePlanner, Skill, StepExecutor, ToolBus, WorkingMemory

@dataclass
class AgentSkeleton:
    name: str = "skeleton-agent"
    planner: SimplePlanner = field(default_factory=SimplePlanner)
    memory: WorkingMemory = field(default_factory=WorkingMemory)
    tools: ToolBus = field(default_factory=ToolBus)
    executor: StepExecutor = field(default_factory=StepExecutor)
    skills: dict[str, Skill] = field(default_factory=dict)
    max_steps: int = 8

    def __post_init__(self) -> None:
        if not self.tools.handlers:
            self.tools.register("weather", lambda city="Berlin": f"{city}: 18C")
            self.tools.register("policy", lambda topic="refund": f"{topic}: 30-day window")
            self.tools.register("echo", lambda text="": text)

    def register_skill(self, skill: Skill) -> None:
        self.skills[skill.name] = skill

    def run(self, goal: str) -> dict[str, Any]:
        plan = self.planner.plan(goal)
        trace = []
        final = ""
        for i, step in enumerate(plan[: self.max_steps]):
            if step == "stop":
                break
            # optional skill hook
            if step in self.skills:
                out = self.skills[step].run(goal)
            else:
                out = self.executor.execute(step, self.tools, goal, self.memory)
            trace.append({"step": i, "name": step, "output": out})
            final = out
        return {"ok": True, "agent": self.name, "plan": plan, "result": final, "trace": trace, "memory": self.memory.context()}
