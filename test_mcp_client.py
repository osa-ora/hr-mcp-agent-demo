import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"]
)

async def main():
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            tools = await session.list_tools()
            print("\nTOOLS:")
            print(tools)

            result = await session.call_tool(
                "get_employee_profile",
                {"employee_number": "EMP001"}
            )

            print("\nRESULT:")
            print(result)

asyncio.run(main())