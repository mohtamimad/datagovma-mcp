"""MCP server entrypoint using streamable HTTP transport."""

from __future__ import annotations

import truststore
from mcp.server.fastmcp import FastMCP

from datagovma_mcp.tools import register_tools
from datagovma_mcp.utils.server_config import get_server_config


def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance."""

    host, port = get_server_config()
    mcp = FastMCP("data.gov.ma MCP server", host=host, port=port, stateless_http=True)
    register_tools(mcp)
    return mcp


def main() -> None:
    # Apply system certificate trust once at server startup.
    truststore.inject_into_ssl()
    server = create_server()
    try:
        server.run(transport="streamable-http")
    except KeyboardInterrupt:
        # Graceful user-initiated shutdown (Ctrl+C) without traceback noise.
        return


if __name__ == "__main__":
    main()
