#!/usr/bin/env python3
import json
from fwloop import demo_loop
def main():
    print(json.dumps(demo_loop().run("demo"), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
