#!/usr/bin/env python3
import json
from fweval import Evaluator, Example, exact_scorer
def main():
    data=[Example("1","hi","hello"), Example("2","bye","bye")]
    ev=Evaluator(exact_scorer, gate=0.5)
    print(json.dumps(ev.evaluate(lambda x: "hello" if x=="hi" else x, data), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
