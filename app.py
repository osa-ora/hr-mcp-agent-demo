import mcp_server

if __name__ == "__main__":
    print("Starting MCP server via FastMCP wrapper...")

    mcp_server.mcp.run(
        transport=mcp_server.MCP_TRANSPORT,
        host=mcp_server.MCP_HOST,
        port=mcp_server.MCP_PORT
    )