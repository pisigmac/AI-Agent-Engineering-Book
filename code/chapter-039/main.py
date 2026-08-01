#!/usr/bin/env python3
import argparse, json
from harness import AgentHarness, demo_agent, Budget
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("goal", nargs="?", default="refund policy")
    p.add_argument("--max-steps", type=int, default=5)
    a=p.parse_args(argv)
    h=AgentHarness(demo_agent, budget=Budget(max_steps=a.max_steps))
    print(json.dumps(h.run(a.goal), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
