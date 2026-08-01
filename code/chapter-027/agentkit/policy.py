"""Simple rule-based policy for the first autonomous agent (offline)."""
from __future__ import annotations
from agentkit.types import Action, Goal, Observation

def decide(goal: Goal, history: list[Observation]) -> Action:
    """Toy autonomy: gather facts then finish with a summary."""
    texts = " ".join(o.content.lower() for o in history)
    g = goal.description.lower()
    if "weather" in g and "weather:" not in texts:
        return Action(kind="act", name="lookup_weather", payload={"city": _city(g)})
    if ("refund" in g or "policy" in g) and "policy:" not in texts:
        return Action(kind="act", name="lookup_policy", payload={"topic": "refund"})
    if not history:
        return Action(kind="act", name="clarify", payload={"question": goal.description})
    # enough evidence
    summary = "; ".join(o.content for o in history[-3:])
    return Action(kind="finish", message=f"Goal complete. Evidence: {summary}")

def _city(text: str) -> str:
    for c in ("berlin", "paris", "tokyo", "london"):
        if c in text:
            return c.title()
    return "Berlin"
