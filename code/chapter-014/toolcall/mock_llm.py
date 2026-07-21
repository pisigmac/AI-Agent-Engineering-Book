"""Scripted LLM that emits tool calls / finals for demos and tests."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class MockToolLLM:
    """Simple policy: if user asks weather for a known pattern, emit tool then final."""

    calls: list[list[dict[str, str]]] = field(default_factory=list)
    _pending_final: str | None = None

    def generate(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(list(messages))
        if self._pending_final is not None:
            msg = self._pending_final
            self._pending_final = None
            return json.dumps({"kind": "final", "message": msg})

        # If last message is a tool observation, produce final from it
        last = messages[-1]["content"] if messages else ""
        if "UNTRUSTED_EVIDENCE" in last and "get_weather" in last:
            # pull temperature from observation JSON if present
            m = re.search(r'"temperature":\s*([0-9.]+)', last)
            city_m = re.search(r'"city":\s*"([^"]+)"', last)
            unit_m = re.search(r'"units":\s*"([^"]+)"', last)
            cond_m = re.search(r'"condition":\s*"([^"]+)"', last)
            if m and city_m:
                city = city_m.group(1)
                temp = m.group(1)
                unit = unit_m.group(1) if unit_m else "C"
                cond = cond_m.group(1) if cond_m else "unknown"
                return json.dumps(
                    {
                        "kind": "final",
                        "message": (
                            f"In {city} it is {temp}°{unit} and {cond} "
                            f"(source: weather tool)."
                        ),
                    }
                )
            if '"ok": false' in last or '"ok":false' in last:
                return json.dumps(
                    {
                        "kind": "final",
                        "message": (
                            "I could not retrieve the weather from the tool. "
                            "Please try a supported city."
                        ),
                    }
                )

        # Only inspect the latest user utterance for intent (avoid system prompt leakage).
        user_text = last_user or ""
        city = _extract_city(user_text)
        units = (
            "imperial"
            if re.search(r"\bfahrenheit\b|\bimperial\b", user_text, re.I)
            else "metric"
        )
        if city:
            return json.dumps(
                {
                    "kind": "tool",
                    "name": "get_weather",
                    "arguments": {"city": city, "units": units},
                }
            )
        if re.search(r"which cities|supported cities|list cities", user_text, re.I):
            return json.dumps(
                {"kind": "tool", "name": "list_supported_cities", "arguments": {}}
            )

        return json.dumps(
            {
                "kind": "final",
                "message": "I can check the weather for supported cities. Which city?",
            }
        )


def _extract_city(text: str) -> str | None:
    for known in ("New York", "Berlin", "Paris", "Tokyo", "Atlantis"):
        if re.search(rf"\b{re.escape(known)}\b", text, re.I):
            return known
    patterns = [
        r"weather (?:in|for)\s+([A-Za-z][A-Za-z]*(?: [A-Za-z]+)?)",
        r"\bin\s+([A-Za-z][A-Za-z]*(?: [A-Za-z]+)?)\s*\??\s*$",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I | re.M)
        if m:
            city = m.group(1).strip().rstrip("?.!")
            city = re.split(r"\s+in\s+", city, maxsplit=1)[0]
            if city.lower() in {"a", "the", "supported", "which"}:
                continue
            return city
    return None
