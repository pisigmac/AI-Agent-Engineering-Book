#!/usr/bin/env python3
import json
from coding import CodingAgent, Workspace, MockLLM


def main() -> int:
    agent = CodingAgent(workspace=Workspace(), llm=MockLLM())
    out = agent.run("add function add(a,b)")
    print(json.dumps({"ok": out["ok"], "files": out["files"], "test": out["test"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
