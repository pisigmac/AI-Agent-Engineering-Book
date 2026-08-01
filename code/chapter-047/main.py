#!/usr/bin/env python3
import argparse, json
from costopt import CostOptimizer
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("prompt", nargs="?", default="summarize ticket")
    p.add_argument("--task", default="")
    a=p.parse_args(argv); opt=CostOptimizer()
    r1=opt.complete(a.prompt, task=a.task); r2=opt.complete(a.prompt, task=a.task)
    print(json.dumps({"first": r1, "second": r2}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
