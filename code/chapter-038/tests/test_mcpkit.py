import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcpkit import MCPClient, demo_server
def test_mcp_flow():
    c=MCPClient(demo_server())
    assert c.initialize()["ok"]
    assert any(t["name"]=="search" for t in c.tools())
    assert c.call_tool("search", q="refund")["ok"]
    assert c.read_resource("kb://refund")["ok"]
    assert "support" in c.prompt("support", issue="late package")["prompt"]
