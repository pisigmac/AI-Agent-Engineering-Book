#!/usr/bin/env python3
import argparse, json
from hitl import HITLController
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--risk", default="high"); p.add_argument("--approve", action="store_true")
    a=p.parse_args(argv); c=HITLController()
    r=c.run_action("issue_refund", {"amount": 40}, risk=a.risk, auto_approve=a.approve)
    print(json.dumps({"result": r, "log": c.log}, indent=2)); return 0 if r.get("ok") else 1
if __name__=="__main__": raise SystemExit(main())
