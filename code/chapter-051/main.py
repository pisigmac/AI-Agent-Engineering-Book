#!/usr/bin/env python3
import json
from crewx.runtime import demo_crew
def main():
    print(json.dumps(demo_crew().kickoff({"topic": "agents"}), indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
