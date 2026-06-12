import os
from dotenv import load_dotenv
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8090")
ORDER_AGGREGATE_PATH = os.getenv("ORDER_AGGREGATE_PATH", "/aggregate")
LAST_ORDERS_PATH = os.getenv("LAST_ORDERS_PATH", "/last")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

MCP_SCHEME = os.getenv("MCP_SCHEME", "http")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_HOST_FOR_CLIENT = os.getenv("MCP_HOST_CLIENT", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
ORDERS_MCP_PORT = int(os.getenv("ORDERS_MCP_PORT", "8001"))
MCP_PATH = os.getenv("MCP_PATH", "/mcp")
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "http")

MCP_ENDPOINT = f"{MCP_SCHEME}://{MCP_HOST_FOR_CLIENT}:{MCP_PORT}{MCP_PATH}"