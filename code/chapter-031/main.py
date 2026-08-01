#!/usr/bin/env python3
import argparse, json
from toolmgr import default_manager
def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    e=sub.add_parser("exec"); e.add_argument("name"); e.add_argument("--args", default="{}"); e.add_argument("--role", default="default")
    a=p.parse_args(argv); m=default_manager()
    if a.cmd=="list": print(json.dumps(m.list(), indent=2)); return 0
    print(json.dumps(m.execute(a.name, json.loads(a.args), roles=(a.role,)), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
