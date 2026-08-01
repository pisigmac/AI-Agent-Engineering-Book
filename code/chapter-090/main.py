#!/usr/bin/env python3
import json
from multiagent import AgentSpec, MultiAgentPlatform, MockLLM


def main() -> int:
    agents = [
        AgentSpec("researcher", ["research", "search"], lambda t, _: f"notes on {t}"),
        AgentSpec("coder", ["code", "implement", "fix"], lambda t, _: f"patch for {t}"),
        AgentSpec("writer", ["write", "summary", "blog"], lambda t, _: f"draft for {t}"),
    ]
    plat = MultiAgentPlatform(agents=agents, llm=MockLLM())
    one = plat.run("implement fix for login")
    many = MultiAgentPlatform(agents=agents, llm=MockLLM()).run("research and write summary", fanout=True)
    print(json.dumps({"single": {"agents": one["agents"], "result": one["result"]},
                      "fanout": {"agents": many["agents"], "result": many["result"]}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
