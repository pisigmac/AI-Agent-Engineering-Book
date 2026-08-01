#!/usr/bin/env python3
import argparse, json
from execloop import default_engine
def main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("goal", nargs="?", default="weather in Berlin")
    print(json.dumps(default_engine().run(p.parse_args(argv).goal), indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
