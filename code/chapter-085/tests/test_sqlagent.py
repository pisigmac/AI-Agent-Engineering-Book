import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlagent import SQLAgent, MockDB, MockLLM, Schema, FORBIDDEN


def _agent():
    schema = Schema(tables={"users": ["id", "name"], "orders": ["id", "user_id", "total"]})
    db = MockDB(
        schema=schema,
        data={
            "users": [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}],
            "orders": [{"id": 10, "user_id": 1, "total": 50}],
        },
    )
    return SQLAgent(db=db, llm=MockLLM())


def test_select_user():
    r = _agent().ask("users named alice")
    assert r["n"] == 1
    assert r["rows"][0]["name"] == "alice"


def test_block_write():
    agent = _agent()
    with pytest.raises(PermissionError):
        agent.db.execute_readonly("DELETE FROM users;")


def test_forbidden_regex():
    assert FORBIDDEN.search("DROP TABLE users")
