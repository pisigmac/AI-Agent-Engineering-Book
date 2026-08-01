#!/usr/bin/env python3
import json
from fwharness import Harness
def agent(goal, ctx):
    if ctx["step"]>=2: return {"done": True, "result": f"done:{goal}"}
    return {"state": {"x":1}}
def main():
    print(json.dumps(Harness(agent).run("task"), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
