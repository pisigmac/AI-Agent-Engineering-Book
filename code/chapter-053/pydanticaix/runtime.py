"""PydanticAI-style typed agent with deps and structured output (offline)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar
from pydantic import BaseModel, Field

class SupportResult(BaseModel):
    intent: str
    answer: str
    confidence: float = Field(ge=0, le=1)

DepsT = TypeVar("DepsT")

@dataclass
class RunContext(Generic[DepsT]):
    deps: DepsT
    prompt: str

@dataclass
class Tool:
    name: str
    fn: Callable[[RunContext[Any], str], str]

@dataclass
class Agent(Generic[DepsT]):
    name: str
    result_type: type[BaseModel]
    deps_type: type
    tools: list[Tool]
    def run_sync(self, prompt: str, *, deps: DepsT) -> dict[str, Any]:
        ctx = RunContext(deps=deps, prompt=prompt)
        tool_notes = []
        for t in self.tools:
            tool_notes.append(t.fn(ctx, prompt))
        intent = "billing" if "refund" in prompt.lower() else "general"
        answer = f"{intent}: " + "; ".join(tool_notes) if tool_notes else prompt
        conf = 0.9 if intent == "billing" else 0.6
        result = self.result_type(intent=intent, answer=answer, confidence=conf)
        return {"ok": True, "framework": "pydantic_ai", "data": result.model_dump(), "usage": {"tools": len(self.tools)}}

@dataclass
class SupportDeps:
    kb: dict[str, str]

def demo_agent() -> Agent[SupportDeps]:
    def search_kb(ctx: RunContext[SupportDeps], q: str) -> str:
        for k, v in ctx.deps.kb.items():
            if k in q.lower():
                return v
        return "no hit"
    return Agent("support", SupportResult, SupportDeps, [Tool("search_kb", search_kb)])
