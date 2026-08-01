#!/usr/bin/env python3
import json
from observ import traced_agent_run
def main():
    print(json.dumps(traced_agent_run("refund"), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
