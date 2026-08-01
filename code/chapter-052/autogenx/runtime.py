"""AutoGen-style multi-agent conversation (offline)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class ConversableAgent:
    name: str
    system_message: str
    human_input_mode: str = "NEVER"  # NEVER|ALWAYS
    reply_fn: Callable[[str, list[dict[str, str]]], str] | None = None
    def generate_reply(self, messages: list[dict[str, str]]) -> str:
        last = messages[-1]["content"] if messages else ""
        if self.reply_fn:
            return self.reply_fn(last, messages)
        return f"{self.name}: ack {last[:60]}"

@dataclass
class GroupChat:
    agents: list[ConversableAgent]
    max_round: int = 4
    def run(self, prompt: str) -> dict[str, Any]:
        messages = [{"role": "user", "name": "user", "content": prompt}]
        speaker_idx = 0
        for r in range(self.max_round):
            agent = self.agents[speaker_idx % len(self.agents)]
            reply = agent.generate_reply(messages)
            messages.append({"role": "assistant", "name": agent.name, "content": reply})
            if "TERMINATE" in reply or r == self.max_round - 1:
                break
            speaker_idx += 1
        return {"ok": True, "framework": "autogen", "messages": messages, "final": messages[-1]["content"]}

def demo_chat() -> GroupChat:
    assistant = ConversableAgent("assistant", "Solve tasks", reply_fn=lambda last, m: f"plan for: {last}")
    executor = ConversableAgent("executor", "Execute", reply_fn=lambda last, m: f"executed | TERMINATE")
    return GroupChat([assistant, executor], max_round=4)
