#!/usr/bin/env python3
import json
from cicdkit import demo_pipeline
def main():
    print(json.dumps(demo_pipeline().run(), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
