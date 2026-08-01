#!/usr/bin/env python3
import json
from autogenx.runtime import demo_chat
def main():
    print(json.dumps(demo_chat().run("analyze logs"), indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
