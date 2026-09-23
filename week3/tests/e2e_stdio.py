"""Live end-to-end check: spawn the week3 server over STDIO and call tools for real.

Verifies the JSON-RPC handshake, tool listing, and a real Open-Meteo call.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> int:
    server_py = Path(__file__).resolve().parents[1] / "server" / "main.py"
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_py)],
        env={"MCP_LOG_LEVEL": "INFO"},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])
            assert {t.name for t in tools.tools} >= {"geocode", "current_weather", "forecast"}

            prompts = await session.list_prompts()
            print("PROMPTS:", [p.name for p in prompts.prompts])

            res = await session.call_tool("geocode", {"place": "Beijing", "count": 2})
            text = res.content[0].text
            print("GEOCODE:", text[:200])
            assert "Beijing" in text

            res2 = await session.call_tool("current_weather", {"place": "Shanghai"})
            print("CURRENT:", res2.content[0].text[:300])
            assert "Temperature" in res2.content[0].text

            res3 = await session.call_tool("forecast", {"place": "Tokyo", "days": 2})
            print("FORECAST:", res3.content[0].text[:300])
            assert "forecast" in res3.content[0].text.lower()

            print("LIVE E2E OK")
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
