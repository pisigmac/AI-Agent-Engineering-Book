#!/usr/bin/env python3
import argparse, json
from graphx import research_graph
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--goal", default="AI agents")
    print(json.dumps(research_graph().run({"goal": p.parse_args(argv).goal}), indent=2, default=str)); return 0
if __name__=="__main__": raise SystemExit(main())
