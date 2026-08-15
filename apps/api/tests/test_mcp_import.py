def test_mcp_server_imports() -> None:
    from project_brain.mcp.server import mcp

    assert type(mcp).__name__ == "MCPServer"
