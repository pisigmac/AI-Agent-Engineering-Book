#!/usr/bin/env python3
import argparse, json
from agentarch import AgentSkeleton
def main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("goal", nargs="?", default="refund policy")
    a = p.parse_args(argv)
    print(json.dumps(AgentSkeleton().run(a.goal), indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
