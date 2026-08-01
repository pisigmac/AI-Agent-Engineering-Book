"""Natural-language to SQL with read-only guards."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import re


FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|ATTACH|DETACH)\b",
    re.I,
)


@dataclass
class Schema:
    tables: dict[str, list[str]]  # table -> columns

    def ddl_summary(self) -> str:
        lines = []
        for t, cols in self.tables.items():
            lines.append(f"TABLE {t}({', '.join(cols)})")
        return "\n".join(lines)


@dataclass
class MockDB:
    schema: Schema
    data: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def execute_readonly(self, sql: str) -> list[dict[str, Any]]:
        if FORBIDDEN.search(sql):
            raise PermissionError("write/DDL not allowed")
        # tiny SELECT parser: SELECT cols FROM table [WHERE col = val]
        m = re.match(
            r"SELECT\s+(.+?)\s+FROM\s+(\w+)(?:\s+WHERE\s+(\w+)\s*=\s*'([^']*)')?\s*;?\s*$",
            sql.strip(),
            re.I | re.S,
        )
        if not m:
            raise ValueError(f"unsupported SQL: {sql}")
        cols_raw, table, where_col, where_val = m.group(1), m.group(2), m.group(3), m.group(4)
        if table not in self.schema.tables:
            raise KeyError(f"unknown table: {table}")
        rows = list(self.data.get(table, []))
        if where_col:
            rows = [r for r in rows if str(r.get(where_col)) == where_val]
        if cols_raw.strip() == "*":
            return rows
        cols = [c.strip() for c in cols_raw.split(",")]
        return [{c: r.get(c) for c in cols} for r in rows]


class LLM(Protocol):
    def nl_to_sql(self, question: str, schema: str) -> str: ...


@dataclass
class MockLLM:
    def nl_to_sql(self, question: str, schema: str) -> str:
        q = question.lower()
        if "users" in q and "alice" in q:
            return "SELECT * FROM users WHERE name = 'alice';"
        if "count" in q and "orders" in q:
            # mock engine doesn't aggregate — return all for demo
            return "SELECT * FROM orders;"
        if "orders" in q:
            return "SELECT * FROM orders;"
        if "users" in q:
            return "SELECT * FROM users;"
        return "SELECT * FROM users;"


@dataclass
class SQLAgent:
    db: MockDB
    llm: LLM
    events: list[dict[str, Any]] = field(default_factory=list)

    def ask(self, question: str) -> dict[str, Any]:
        schema = self.db.schema.ddl_summary()
        sql = self.llm.nl_to_sql(question, schema).strip()
        self.events.append({"type": "sql_generated", "sql": sql})
        if FORBIDDEN.search(sql):
            self.events.append({"type": "blocked", "sql": sql})
            raise PermissionError(f"blocked SQL: {sql}")
        # only allow known tables
        tables = set(self.db.schema.tables)
        for t in re.findall(r"\bFROM\s+(\w+)", sql, flags=re.I):
            if t not in tables:
                raise PermissionError(f"table not allowlisted: {t}")
        rows = self.db.execute_readonly(sql)
        self.events.append({"type": "executed", "n": len(rows)})
        return {"sql": sql, "rows": rows, "n": len(rows)}
