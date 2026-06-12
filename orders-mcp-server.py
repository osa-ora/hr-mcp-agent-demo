import os
import httpx
import asyncio
from fastmcp import FastMCP
from configorders import MCP_HOST, ORDERS_MCP_PORT, MCP_TRANSPORT, ORDER_AGGREGATE_PATH, LAST_ORDERS_PATH, REQUEST_TIMEOUT, API_BASE_URL



# =========================================================
# INTERNAL REST CLIENT (NO EXTRA FILE)
# =========================================================

def rest_get(path: str, params: dict | None = None):

    url = f"{API_BASE_URL}{path}"

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        resp = client.get(url, params=params)

    resp.raise_for_status()
    return resp.json()

# =========================================================
# MCP SERVER
# =========================================================

mcp = FastMCP("Orders MCP")

# ---------------------------------------------------------
# TOOL 1: Aggregate Orders
# ---------------------------------------------------------

@mcp.tool(
    annotations={"skill": "kafka-query"},
    description="Get order aggregates for last N seconds. Only valid parameter is 'seconds' (int)."
)
def get_order_aggregate(seconds: int):

    return rest_get(
        ORDER_AGGREGATE_PATH,
        {"seconds": seconds}
    )

# ---------------------------------------------------------
# TOOL 2: Last Orders
# ---------------------------------------------------------

@mcp.tool(
    annotations={"skill": "kafka-query"},
    description="Get last N orders. Only valid parameter is 'size' (int, default 10)."
)
def get_last_orders(size: int = 10):

    return rest_get(
        LAST_ORDERS_PATH,
        {"size": size}
    )

# =========================================================
# MAIN ENTRY
# =========================================================
if __name__ == "__main__":
    print("REGISTERED TOOLS:", mcp.list_tools())

    mcp.run(
        transport=MCP_TRANSPORT,
        host=MCP_HOST,
        port=ORDERS_MCP_PORT
    )