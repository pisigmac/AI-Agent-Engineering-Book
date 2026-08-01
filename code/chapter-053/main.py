#!/usr/bin/env python3
import json
from pydanticaix.runtime import demo_agent, SupportDeps
def main():
    agent = demo_agent()
    deps = SupportDeps(kb={"refund": "30 day refund window"})
    print(json.dumps(agent.run_sync("refund status", deps=deps), indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
