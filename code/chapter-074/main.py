#!/usr/bin/env python3
import json
from fwworkflow import WorkflowEngine, Step
def main():
    w=WorkflowEngine(); w.add(Step("a", lambda s: {"x":1})); w.add(Step("b", lambda s: {"y": s["x"]+1})); print(json.dumps(w.run(), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
