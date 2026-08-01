#!/usr/bin/env python3
import json
from fwtools import default_registry
def main():
    r=default_registry(); print(json.dumps({"list": r.list(), "add": r.call("add", {"a":2,"b":3})}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
