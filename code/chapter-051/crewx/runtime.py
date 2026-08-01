"""CrewAI-style crew of role agents and tasks (offline)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class Agent:
    role: str
    goal: str
    backstory: str = ""
    tool: Callable[[str], str] | None = None

@dataclass
class Task:
    description: str
    agent: str
    expected_output: str = ""

@dataclass
class Crew:
    agents: dict[str, Agent]
    tasks: list[Task]
    process: str = "sequential"
    def kickoff(self, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(inputs or {})
        outputs = []
        for task in self.tasks:
            agent = self.agents[task.agent]
            raw = f"{agent.role} working on {task.description} for {ctx.get('topic','')}"
            if agent.tool:
                raw = agent.tool(raw)
            outputs.append({"task": task.description, "agent": agent.role, "output": raw})
            ctx["last"] = raw
        return {"ok": True, "framework": "crewai", "process": self.process, "outputs": outputs, "final": ctx.get("last")}

def demo_crew() -> Crew:
    return Crew(
        agents={
            "researcher": Agent("Researcher", "Find facts", tool=lambda s: s + " | notes:ok"),
            "writer": Agent("Writer", "Write summary"),
        },
        tasks=[
            Task("Gather sources", "researcher"),
            Task("Write brief", "writer"),
        ],
    )
