"""Lightweight coding agent over an in-memory workspace."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import re


@dataclass
class Workspace:
    files: dict[str, str] = field(default_factory=dict)

    def read(self, path: str) -> str:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def write(self, path: str, content: str) -> None:
        self.files[path] = content

    def list_files(self) -> list[str]:
        return sorted(self.files)


@dataclass
class TestRunner:
    """Runs simple assertion snippets embedded in tests.py style content."""

    def run(self, ws: Workspace, test_path: str = "tests.py") -> dict[str, Any]:
        if test_path not in ws.files:
            return {"ok": False, "error": "no tests"}
        # Execute tests in restricted namespace with workspace files loaded as modules-like dict
        ns: dict[str, Any] = {"__name__": "tests"}
        # expose other files as simple string constants for demos
        for p, c in ws.files.items():
            if p.endswith(".py") and p != test_path:
                try:
                    exec(compile(c, p, "exec"), ns)  # noqa: S102 — intentional sandbox demo
                except Exception as e:  # noqa: BLE001
                    return {"ok": False, "error": f"import {p}: {e}"}
        try:
            exec(compile(ws.files[test_path], test_path, "exec"), ns)  # noqa: S102
        except AssertionError as e:
            return {"ok": False, "error": f"assert: {e}"}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)}
        return {"ok": True, "error": None}


class LLM(Protocol):
    def plan(self, goal: str, files: list[str]) -> list[dict[str, str]]: ...


@dataclass
class MockLLM:
    def plan(self, goal: str, files: list[str]) -> list[dict[str, str]]:
        g = goal.lower()
        if "add" in g and "add" in g and "function" in g:
            # add add(a,b) to mathutil.py
            return [
                {
                    "action": "write",
                    "path": "mathutil.py",
                    "content": "def add(a, b):\n    return a + b\n",
                },
                {
                    "action": "write",
                    "path": "tests.py",
                    "content": "assert add(2, 3) == 5\nassert add(0, 0) == 0\n",
                },
            ]
        if "fix" in g and "multiply" in g:
            return [
                {
                    "action": "write",
                    "path": "mathutil.py",
                    "content": "def multiply(a, b):\n    return a * b\n",
                },
                {
                    "action": "write",
                    "path": "tests.py",
                    "content": "assert multiply(3, 4) == 12\n",
                },
            ]
        return [{"action": "noop", "path": "", "content": ""}]


@dataclass
class CodingAgent:
    workspace: Workspace
    llm: LLM
    runner: TestRunner = field(default_factory=TestRunner)
    max_iters: int = 3
    events: list[dict[str, Any]] = field(default_factory=list)

    def run(self, goal: str) -> dict[str, Any]:
        self.events.append({"type": "start", "goal": goal})
        last_test: dict[str, Any] = {"ok": False, "error": "not run"}
        for i in range(self.max_iters):
            steps = self.llm.plan(goal, self.workspace.list_files())
            self.events.append({"type": "plan", "iter": i, "steps": len(steps)})
            for step in steps:
                if step.get("action") == "write" and step.get("path"):
                    self.workspace.write(step["path"], step["content"])
                    self.events.append({"type": "write", "path": step["path"]})
            last_test = self.runner.run(self.workspace)
            self.events.append({"type": "test", "iter": i, **last_test})
            if last_test.get("ok"):
                break
        return {
            "goal": goal,
            "ok": bool(last_test.get("ok")),
            "files": self.workspace.list_files(),
            "test": last_test,
            "events": self.events,
        }
