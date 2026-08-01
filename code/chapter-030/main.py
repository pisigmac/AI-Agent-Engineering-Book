#!/usr/bin/env python3
import argparse, json
from skillreg import default_registry
def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list"); r=sub.add_parser("run"); r.add_argument("skill"); r.add_argument("text")
    c=sub.add_parser("compose"); c.add_argument("text"); c.add_argument("--skills", default="normalize,summarize,cite")
    a=p.parse_args(argv); reg=default_registry()
    if a.cmd=="list": print(json.dumps(reg.list(), indent=2)); return 0
    if a.cmd=="run": print(json.dumps({"result": reg.get(a.skill).run(text=a.text)}, indent=2)); return 0
    print(json.dumps({"result": reg.compose(a.skills.split(","), a.text)}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
