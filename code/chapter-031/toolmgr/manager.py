"""Production tool manager: registry, permissions, sandbox flags, validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[..., Any]
    permissions: tuple[str, ...] = ("default",)
    sandboxed: bool = True
    schema: dict[str, type] = field(default_factory=dict)

class ToolManager:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
    def list(self) -> list[dict[str, Any]]:
        return [{"name": t.name, "description": t.description, "permissions": list(t.permissions), "sandboxed": t.sandboxed} for t in self._tools.values()]
    def validate(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            return {"ok": False, "error": "unknown_tool"}
        tool = self._tools[name]
        for k, typ in tool.schema.items():
            if k not in args:
                return {"ok": False, "error": f"missing:{k}"}
            if not isinstance(args[k], typ):
                return {"ok": False, "error": f"type:{k}"}
        return {"ok": True}
    def execute(self, name: str, args: dict[str, Any], *, roles: tuple[str, ...] = ("default",)) -> dict[str, Any]:
        v = self.validate(name, args)
        if not v["ok"]:
            return v
        tool = self._tools[name]
        if not set(tool.permissions) & set(roles) and "admin" not in roles:
            return {"ok": False, "error": "permission_denied"}
        try:
            result = tool.handler(**args)
            return {"ok": True, "result": result, "sandboxed": tool.sandboxed}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"execution_error:{e}"}

def default_manager() -> ToolManager:
    m = ToolManager()
    m.register(Tool("get_weather", "weather by city", lambda city: f"{city}: 18C", schema={"city": str}))
    m.register(Tool("search_kb", "kb search", lambda q: [f"hit:{q}"], schema={"q": str}, permissions=("default","support")))
    m.register(Tool("run_shell", "dangerous", lambda cmd: f"blocked:{cmd}", permissions=("admin",), sandboxed=False, schema={"cmd": str}))
    return m
