#!/usr/bin/env python3
import json
from scalekit import demo_scale
def main():
    print(json.dumps(demo_scale(), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
