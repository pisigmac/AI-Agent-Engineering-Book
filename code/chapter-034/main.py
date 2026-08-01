#!/usr/bin/env python3
import argparse, json
from reflect import ReflectionEngine
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("answer"); p.add_argument("--evidence", default=""); p.add_argument("--goal", default="")
    a=p.parse_args(argv); print(json.dumps(ReflectionEngine().reflect(a.answer, evidence=a.evidence, goal=a.goal).to_dict(), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
