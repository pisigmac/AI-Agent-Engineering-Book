#!/usr/bin/env python3
import argparse, json
from mcpkit import MCPClient, demo_server
def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init"); sub.add_parser("tools"); sub.add_parser("resources")
    t=sub.add_parser("call"); t.add_argument("name"); t.add_argument("--q", default="refund")
    r=sub.add_parser("read"); r.add_argument("uri", nargs="?", default="kb://refund")
    a=p.parse_args(argv); c=MCPClient(demo_server())
    if a.cmd=="init": print(json.dumps(c.initialize(), indent=2)); return 0
    if a.cmd=="tools": print(json.dumps(c.tools(), indent=2)); return 0
    if a.cmd=="resources": print(json.dumps(c.resources(), indent=2)); return 0
    if a.cmd=="call":
        args={"q": a.q} if a.name=="search" else {"city": a.q}
        print(json.dumps(c.call_tool(a.name, **args), indent=2)); return 0
    print(json.dumps(c.read_resource(a.uri), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
