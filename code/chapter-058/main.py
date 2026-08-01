#!/usr/bin/env python3
import json, tempfile
from dockerkit import write_assets
def main():
    d = tempfile.mkdtemp(prefix="docker-")
    print(json.dumps(write_assets(d), indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
