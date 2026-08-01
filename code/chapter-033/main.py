#!/usr/bin/env python3
import argparse, json
from memsys import MemorySystem
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--demo", action="store_true")
    a=p.parse_args(argv); m=MemorySystem()
    m.remember_turn("refund?", "30 day policy")
    m.remember_fact("Refunds available within 30 days", topic="billing")
    print(json.dumps(m.context("refund"), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
