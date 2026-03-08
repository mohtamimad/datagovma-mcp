"""MCP server entrypoint using streamable HTTP transport."""

from __future__ import annotations

import truststore
from mcp.server.fastmcp import FastMCP

from tools import register_tools

mcp = FastMCP("data.gov.ma MCP server")
register_tools(mcp)


def main() -> None:
    # Apply system certificate trust once at server startup.
    truststore.inject_into_ssl()
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
