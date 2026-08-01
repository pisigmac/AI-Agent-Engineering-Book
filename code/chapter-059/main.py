#!/usr/bin/env python3
import json
from pgkit import AgentStore
def main():
    s=AgentStore(); s.upsert_agent("a1","support"); s.create_run("r1","a1","refund"); s.finish_run("r1","succeeded","30 days")
    print(json.dumps(s.get_run("r1"), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
