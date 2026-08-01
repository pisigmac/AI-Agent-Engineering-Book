"""Environment that executes actions and returns observations."""
from __future__ import annotations
from agentkit.types import Action, Observation

_WEATHER = {"Berlin": "18C cloudy", "Paris": "20C clear", "Tokyo": "24C rain", "London": "15C fog"}
_POLICY = {"refund": "Refunds within 30 days for unused products."}

def execute(action: Action) -> Observation:
    if action.kind != "act":
        return Observation(content="no-op", source="env", ok=True)
    if action.name == "lookup_weather":
        city = str(action.payload.get("city", "Berlin"))
        return Observation(content=f"weather:{city}={_WEATHER.get(city, 'unknown')}", source="weather")
    if action.name == "lookup_policy":
        topic = str(action.payload.get("topic", "refund"))
        return Observation(content=f"policy:{_POLICY.get(topic, 'n/a')}", source="policy")
    if action.name == "clarify":
        return Observation(content=f"clarified:{action.payload.get('question','')}", source="user")
    return Observation(content=f"unknown_action:{action.name}", source="env", ok=False)
