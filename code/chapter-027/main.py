#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from agentkit import AutonomousAgent, Goal

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Chapter 27 — first autonomous agent")
    p.add_argument("goal", nargs="?", default="What is the weather in Berlin?")
    p.add_argument("--max-steps", type=int, default=6)
    args = p.parse_args(argv)
    r = AutonomousAgent(max_steps=args.max_steps).run(Goal(description=args.goal))
    print(json.dumps(r.to_dict(), indent=2))
    return 0 if r.ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
