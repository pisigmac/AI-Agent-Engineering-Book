#!/usr/bin/env python3
import argparse, json
from multiagent import research_assistant
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("goal", nargs="?", default="AI agent memory systems")
    print(json.dumps(research_assistant().run(p.parse_args(argv).goal), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
