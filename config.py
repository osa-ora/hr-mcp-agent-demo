import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

MODEL_NAME = os.getenv("MODEL_NAME", "llama3.1")
MAX_STEPS = int(os.getenv("MAX_STEPS", "9"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

MCP_SCHEME = os.getenv("MCP_SCHEME", "http")
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_PATH = os.getenv("MCP_PATH", "/sse")
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "sse")

MCP_ENDPOINT = f"{MCP_SCHEME}://{MCP_HOST}:{MCP_PORT}{MCP_PATH}"