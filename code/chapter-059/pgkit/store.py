"""PostgreSQL-shaped persistence using sqlite for offline tests + SQL schema."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  goal TEXT NOT NULL,
  status TEXT NOT NULL,
  result TEXT,
  FOREIGN KEY(agent_id) REFERENCES agents(id)
);
"""

class AgentStore:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
    def upsert_agent(self, agent_id: str, name: str) -> None:
        self.conn.execute(
            "INSERT INTO agents(id,name,created_at) VALUES(?,?,datetime('now')) ON CONFLICT(id) DO UPDATE SET name=excluded.name",
            (agent_id, name),
        )
        self.conn.commit()
    def create_run(self, run_id: str, agent_id: str, goal: str) -> None:
        self.conn.execute(
            "INSERT INTO runs(id,agent_id,goal,status) VALUES(?,?,?,?)",
            (run_id, agent_id, goal, "running"),
        )
        self.conn.commit()
    def finish_run(self, run_id: str, status: str, result: str) -> None:
        self.conn.execute("UPDATE runs SET status=?, result=? WHERE id=?", (status, result, run_id))
        self.conn.commit()
    def get_run(self, run_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        return dict(row) if row else None
    def list_runs(self, agent_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM runs WHERE agent_id=? ORDER BY id", (agent_id,)).fetchall()
        return [dict(r) for r in rows]
