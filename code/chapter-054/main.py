#!/usr/bin/env python3
import json
from skernelx.runtime import demo_kernel
def main():
    print(json.dumps(demo_kernel().run_plan("weather today"), indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
