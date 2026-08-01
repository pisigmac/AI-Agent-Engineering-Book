"""First autonomous agent: goal-directed loop with bounded steps."""
from __future__ import annotations
from agentkit import env, policy
from agentkit.types import AgentResult, AgentState, Goal, Observation

class AutonomousAgent:
    def __init__(self, *, max_steps: int = 6) -> None:
        if max_steps < 1:
            raise ValueError("max_steps >= 1")
        self.max_steps = max_steps
        self.state = AgentState.CREATED
        self.history: list[Observation] = []

    def run(self, goal: Goal | str) -> AgentResult:
        if isinstance(goal, str):
            goal = Goal(description=goal)
        self.state = AgentState.RUNNING
        self.history = []
        steps: list[dict] = []
        for i in range(self.max_steps):
            action = policy.decide(goal, self.history)
            steps.append({"step": i, "action": action.kind, "name": action.name, "payload": action.payload})
            if action.kind == "finish":
                self.state = AgentState.SUCCEEDED
                return AgentResult(True, self.state, action.message, steps)
            if action.kind == "fail":
                self.state = AgentState.FAILED
                return AgentResult(False, self.state, action.message or "failed", steps)
            obs = env.execute(action)
            self.history.append(obs)
            steps.append({"step": i, "observation": obs.content, "ok": obs.ok})
            if not obs.ok:
                self.state = AgentState.FAILED
                return AgentResult(False, self.state, obs.content, steps)
        self.state = AgentState.FAILED
        return AgentResult(False, self.state, "max_steps_exceeded", steps)
