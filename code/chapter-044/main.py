#!/usr/bin/env python3
import json
from ageval import evaluate, demo_agent, DEFAULT_CASES
def main():
    print(json.dumps(evaluate(demo_agent, DEFAULT_CASES), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
