"""
Quick manual test for the MCP server mounted at /mcp.

This acts like an MCP CLIENT would (e.g. Claude Desktop): it connects to
our running FastAPI server's /mcp endpoint over Streamable HTTP, lists the
available tools, then calls a couple of them.

How to run:
    1. Start the backend as usual:  uvicorn app.main:app --reload
    2. In another terminal (same venv), run:  python test_mcp_client.py

It will:
    - log in via the normal REST API (/api/v1/auth/login) to get a JWT
    - connect to the MCP server and list all 6 tools
    - call search_hcp and analyze_trends as a smoke test

Edit EVAL_EMAIL / EVAL_PASSWORD below to match a real user in your DB
(the same ones you used for evaluation/evaluate_agent.py work fine).
"""

import asyncio
import os

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
EVAL_EMAIL = os.getenv("EVAL_EMAIL", "emvs2005@gmail.com")
EVAL_PASSWORD = os.getenv("EVAL_PASSWORD", "123456")


async def get_token() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": EVAL_EMAIL, "password": EVAL_PASSWORD},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["access_token"]


async def main():
    print(f"Logging in as {EVAL_EMAIL} ...")
    token = await get_token()
    print("Got token.\n")

    mcp_url = f"{BASE_URL}/mcp"
    print(f"Connecting to MCP server at {mcp_url} ...")

    async with streamablehttp_client(mcp_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available MCP tools:")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description.splitlines()[0]}")
            print()

            print("Calling search_hcp(query='Chen') ...")
            result = await session.call_tool(
                "search_hcp", {"token": token, "query": "Chen"}
            )
            print(result.content[0].text)
            print()

            print("Calling analyze_trends(days=30) ...")
            result = await session.call_tool(
                "analyze_trends", {"token": token, "days": 30}
            )
            print(result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())