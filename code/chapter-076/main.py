#!/usr/bin/env python3
import json
from fwreflect import ReflectionEngine
def main():
    print(json.dumps(ReflectionEngine().critique("ok", evidence="refunds within 30 days"), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
