import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME", "hrdb")
DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.1")
MAX_STEPS = int(os.getenv("MAX_STEPS", "9"))
#DEBUG = True
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

MCP_SCHEME = os.getenv("MCP_SCHEME", "http")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.1")
MCP_HOST_FOR_CLIENT = os.getenv("MCP_HOST_CLIENT", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_PATH = os.getenv("MCP_PATH", "/mcp")
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "http")

MCP_ENDPOINT = f"{MCP_SCHEME}://{MCP_HOST_FOR_CLIENT}:{MCP_PORT}{MCP_PATH}"