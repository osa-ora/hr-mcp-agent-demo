# pip install mcp-compressor
from mcp_compressor import CompressorClient

with CompressorClient(
    servers={"alpha": {"command": "python", "args": ["app.py"]}},
    compression_level="medium",
) as proxy:
    print([tool.name for tool in proxy.tools])
    print(proxy.invoke("echo", {"message": "hello"}))