#!/usr/bin/env python3
import json
from fwskills import default_registry
def main():
    r=default_registry(); print(json.dumps({"out": r.compose(["lower","exclaim"], "Hi"), "tags": r.discover("text")}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
