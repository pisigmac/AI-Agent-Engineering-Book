#!/usr/bin/env python3
import json
from oaiagents.runtime import demo
def main():
    print(json.dumps(demo().run("support", "weather please"), indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
