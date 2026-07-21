"""Tool-calling agent loop."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from toolcall.executor import ToolExecutor
from toolcall.registry import ToolRegistry
from toolcall.specs import LoopResult, ToolSpec
from toolcall.validate_call import parse_agent_turn
from toolcall.weather import (
    GetWeatherArgs,
    ListCitiesArgs,
    get_weather,
    list_supported_cities,
)

GenerateFn = Callable[[list[dict[str, str]]], str]


class ToolLoop:
    def __init__(
        self,
        registry: ToolRegistry,
        generate: GenerateFn,
        *,
        max_steps: int = 6,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        self.registry = registry
        self.generate = generate
        self.executor = ToolExecutor(registry)
        self.max_steps = max_steps

    def run(self, user_message: str, *, system: str | None = None) -> LoopResult:
        system = system or (
            "You are a weather assistant. Use tools for factual weather. "
            "Never invent temperatures. When done, return kind=final."
        )
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": system + "\n\n" + self.registry.descriptions_for_prompt(),
            },
            {"role": "user", "content": user_message},
        ]
        steps: list[dict[str, Any]] = []

        for step in range(self.max_steps):
            raw = self.generate(messages)
            try:
                data = json.loads(raw)
                turn = parse_agent_turn(data)
            except Exception as exc:  # noqa: BLE001
                steps.append(
                    {
                        "step": step,
                        "error": f"bad_model_output: {exc}",
                        "raw": raw[:200],
                    }
                )
                messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Invalid action JSON. Return either "
                            '{"kind":"tool","name":...,"arguments":{...}} '
                            'or {"kind":"final","message":...}'
                        ),
                    }
                )
                continue

            if turn.kind == "final":
                msg = (turn.message or "").strip() or "Done."
                steps.append({"step": step, "kind": "final", "message": msg})
                return LoopResult(
                    final_message=msg, steps=steps, ok=True, stop_reason="final"
                )

            name = turn.name or ""
            obs = self.executor.execute(name, turn.arguments)
            steps.append(
                {
                    "step": step,
                    "kind": "tool",
                    "name": name,
                    "arguments": turn.arguments,
                    "observation_ok": obs.ok,
                    "error_code": obs.error_code,
                    "latency_s": round(obs.latency_s, 4),
                }
            )
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": obs.to_message_content()})

        return LoopResult(
            final_message=(
                "I hit my tool-step budget before finishing. Please try a simpler request."
            ),
            steps=steps,
            ok=False,
            stop_reason="max_steps",
        )


def build_weather_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        ToolSpec(
            name="get_weather",
            description="Get current weather for a supported city.",
            args_model=GetWeatherArgs,
            handler=get_weather,
            timeout_s=2.0,
            permissions=("weather:read",),
        )
    )
    reg.register(
        ToolSpec(
            name="list_supported_cities",
            description="List cities available in the weather database.",
            args_model=ListCitiesArgs,
            handler=lambda: list_supported_cities(),
            timeout_s=1.0,
            permissions=("weather:read",),
        )
    )
    return reg


def weather_assistant(user_message: str, generate: GenerateFn | None = None) -> LoopResult:
    from toolcall.mock_llm import MockToolLLM

    reg = build_weather_registry()
    gen = generate or MockToolLLM().generate
    return ToolLoop(reg, gen, max_steps=6).run(user_message)
