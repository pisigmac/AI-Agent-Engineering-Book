#!/usr/bin/env python3
"""Chapter 14 CLI — function calling / weather assistant."""

from __future__ import annotations

import argparse
import json

from toolcall.loop import build_weather_registry, weather_assistant
from toolcall.registry import ToolRegistry


def cmd_tools() -> int:
    reg = build_weather_registry()
    print(json.dumps({"tools": reg.export_schemas()}, indent=2))
    return 0


def cmd_weather(city: str, units: str) -> int:
    result = weather_assistant(f"What is the weather in {city} in {units}?")
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0 if result.ok else 1


def cmd_chat(message: str) -> int:
    result = weather_assistant(message)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0 if result.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 14 — tool calling")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tools", help="List tool JSON schemas")
    p_w = sub.add_parser("weather", help="Weather for a city")
    p_w.add_argument("--city", required=True)
    p_w.add_argument("--units", default="celsius", choices=["celsius", "fahrenheit"])
    p_c = sub.add_parser("chat", help="Free-form weather assistant message")
    p_c.add_argument("--message", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "tools":
        return cmd_tools()
    if args.cmd == "weather":
        units = "imperial" if args.units == "fahrenheit" else "metric"
        # pass units via message for mock LLM
        msg = f"What's the weather in {args.city}"
        if units == "imperial":
            msg += " in fahrenheit"
        return cmd_chat(msg)
    if args.cmd == "chat":
        return cmd_chat(args.message)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
