#!/usr/bin/env python3
import json
from sqlagent import SQLAgent, MockDB, MockLLM, Schema


def main() -> int:
    schema = Schema(tables={"users": ["id", "name"], "orders": ["id", "user_id", "total"]})
    db = MockDB(
        schema=schema,
        data={
            "users": [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}],
            "orders": [{"id": 10, "user_id": 1, "total": 50}],
        },
    )
    agent = SQLAgent(db=db, llm=MockLLM())
    print(json.dumps(agent.ask("show users named alice"), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
