#!/usr/bin/env python3
import json
from tracekit import demo_trace
def main():
    print(json.dumps(demo_trace(), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
