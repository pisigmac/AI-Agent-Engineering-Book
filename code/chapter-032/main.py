#!/usr/bin/env python3
import argparse, json
from planner import PlanExecutor
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("goal", nargs="?", default="research compare options")
    p.add_argument("--strategy", default="plan_execute", choices=["plan_execute","react"])
    a=p.parse_args(argv); print(json.dumps(PlanExecutor().run(a.goal, strategy=a.strategy), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
