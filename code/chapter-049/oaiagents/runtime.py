"""OpenAI Agents SDK conceptual runtime (offline)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[..., Any]

@dataclass
class Agent:
    name: str
    instructions: str
    tools: list[Tool] = field(default_factory=list)
    handoffs: list[str] = field(default_factory=list)

@dataclass
class Runner:
    agents: dict[str, Agent]
    def run(self, agent_name: str, user_input: str, *, max_turns: int = 4) -> dict[str, Any]:
        agent = self.agents[agent_name]
        trace = [{"role": "user", "content": user_input}]
        # scripted tool use for demo
        for turn in range(max_turns):
            if "weather" in user_input.lower() and any(t.name == "get_weather" for t in agent.tools):
                tool = next(t for t in agent.tools if t.name == "get_weather")
                obs = tool.handler(city="Berlin")
                trace.append({"role": "tool", "name": tool.name, "content": obs})
                final = f"Based on tool: {obs}"
                trace.append({"role": "assistant", "content": final})
                return {"ok": True, "framework": "openai_agents_sdk", "final": final, "trace": trace, "agent": agent.name}
            if agent.handoffs and "specialist" in user_input.lower():
                return self.run(agent.handoffs[0], user_input, max_turns=max_turns-1)
            final = f"{agent.name}: {agent.instructions[:40]}... => handled: {user_input}"
            trace.append({"role": "assistant", "content": final})
            return {"ok": True, "framework": "openai_agents_sdk", "final": final, "trace": trace, "agent": agent.name}
        return {"ok": False, "framework": "openai_agents_sdk", "final": None, "trace": trace}

def demo() -> Runner:
    weather = Tool("get_weather", "city weather", lambda city="Berlin": f"{city}:18C")
    support = Agent("support", "You are support.", tools=[weather], handoffs=["billing"])
    billing = Agent("billing", "You handle refunds.")
    return Runner({"support": support, "billing": billing})
