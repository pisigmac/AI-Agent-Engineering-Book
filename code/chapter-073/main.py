#!/usr/bin/env python3
import json
from fwmemory import MemoryEngine
def main():
    m=MemoryEngine(); m.add_turn("user: refund?"); m.remember("Refunds within 30 days"); print(json.dumps(m.context("refund"), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
