#!/usr/bin/env python3
import json
from adkx.runtime import demo_runner
def main():
    print(json.dumps(demo_runner().run("u1", "s1", "search docs"), indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
