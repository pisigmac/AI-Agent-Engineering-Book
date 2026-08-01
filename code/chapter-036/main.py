#!/usr/bin/env python3
import argparse, json
from workflow import demo_workflow
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--text", default="I need a refund")
    print(json.dumps(demo_workflow().run({"text": p.parse_args(argv).text}), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
