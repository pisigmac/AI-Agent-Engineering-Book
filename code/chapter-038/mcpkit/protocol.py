"""Minimal MCP-style client/server: tools, resources, prompts over in-process transport."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class MCPTool:
    name: str
    description: str
    handler: Callable[..., Any]
    input_schema: dict[str, Any] = field(default_factory=dict)

@dataclass
class MCPResource:
    uri: str
    name: str
    text: str
    mime_type: str = "text/plain"

class MCPServer:
    def __init__(self, name: str = "demo-mcp") -> None:
        self.name = name
        self.tools: dict[str, MCPTool] = {}
        self.resources: dict[str, MCPResource] = {}
        self.prompts: dict[str, str] = {}
    def add_tool(self, tool: MCPTool) -> None:
        self.tools[tool.name] = tool
    def add_resource(self, resource: MCPResource) -> None:
        self.resources[resource.uri] = resource
    def add_prompt(self, name: str, template: str) -> None:
        self.prompts[name] = template
    def list_tools(self) -> list[dict[str, Any]]:
        return [{"name": t.name, "description": t.description, "input_schema": t.input_schema} for t in self.tools.values()]
    def list_resources(self) -> list[dict[str, Any]]:
        return [{"uri": r.uri, "name": r.name, "mime_type": r.mime_type} for r in self.resources.values()]
    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if name not in self.tools:
            return {"ok": False, "error": "unknown_tool"}
        try:
            result = self.tools[name].handler(**(arguments or {}))
            return {"ok": True, "content": result}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)}
    def read_resource(self, uri: str) -> dict[str, Any]:
        if uri not in self.resources:
            return {"ok": False, "error": "unknown_resource"}
        r = self.resources[uri]
        return {"ok": True, "uri": r.uri, "text": r.text, "mime_type": r.mime_type}
    def get_prompt(self, name: str, **vars: Any) -> dict[str, Any]:
        if name not in self.prompts:
            return {"ok": False, "error": "unknown_prompt"}
        try:
            return {"ok": True, "prompt": self.prompts[name].format(**vars)}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)}

class MCPClient:
    """In-process transport client (production: stdio/HTTP SSE)."""
    def __init__(self, server: MCPServer) -> None:
        self.server = server
    def initialize(self) -> dict[str, Any]:
        return {"ok": True, "server": self.server.name, "protocol": "mcp-lite/1.0"}
    def tools(self): return self.server.list_tools()
    def resources(self): return self.server.list_resources()
    def call_tool(self, name: str, **arguments: Any) -> dict[str, Any]:
        return self.server.call_tool(name, arguments)
    def read_resource(self, uri: str) -> dict[str, Any]:
        return self.server.read_resource(uri)
    def prompt(self, name: str, **vars: Any) -> dict[str, Any]:
        return self.server.get_prompt(name, **vars)

def demo_server() -> MCPServer:
    s = MCPServer("kb-mcp")
    s.add_tool(MCPTool("search", "search knowledge", lambda q: [f"result:{q}"], {"q": "string"}))
    s.add_tool(MCPTool("weather", "get weather", lambda city="Berlin": f"{city}:18C", {"city": "string"}))
    s.add_resource(MCPResource("kb://refund", "Refund Policy", "Refunds within 30 days for unused products."))
    s.add_prompt("support", "You are support. User issue: {issue}")
    return s
