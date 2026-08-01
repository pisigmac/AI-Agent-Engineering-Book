#!/usr/bin/env python3
import json
from eventbus import demo_ticket_flow
def main():
    print(json.dumps(demo_ticket_flow(), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
