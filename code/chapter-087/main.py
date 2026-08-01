#!/usr/bin/env python3
import json
from meeting import MeetingAssistant, Transcript, MockLLM


def main() -> int:
    t = Transcript(
        meeting_id="m1",
        title="Sprint planning",
        lines=[
            "Ada: We need to ship the API.",
            "Bob: Decided we will use FastAPI.",
            "Ada: Bob will write the OpenAPI spec by Friday.",
            "ACTION: Ada: review PR #12",
        ],
    )
    report = MeetingAssistant(llm=MockLLM()).process(t)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
