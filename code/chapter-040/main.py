#!/usr/bin/env python3
import argparse, json
from modechoice import run_selected, select_mode
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("task", nargs="?", default="research competitor landscape")
    p.add_argument("--decide-only", action="store_true")
    a=p.parse_args(argv)
    print(json.dumps(select_mode(a.task).to_dict() if a.decide_only else run_selected(a.task), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
