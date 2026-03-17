"""MCP server entrypoint using streamable HTTP transport."""

from __future__ import annotations

import logging

import truststore
from mcp.server.fastmcp import FastMCP

from datagovma_mcp.tools import register_tools
from datagovma_mcp.utils.logging_config import configure_logging
from datagovma_mcp.utils.server_config import get_server_config

logger = logging.getLogger(__name__)


def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance."""

    host, port = get_server_config()
    logger.info("Creating MCP server on %s:%s", host, port)
    mcp = FastMCP("data.gov.ma MCP server", host=host, port=port, stateless_http=True)
    register_tools(mcp)
    logger.debug("MCP tools registered")
    return mcp


def main() -> None:
    log_level = configure_logging()
    logger.info("Starting data.gov.ma MCP server with log level %s", log_level)
    # Apply system certificate trust once at server startup.
    truststore.inject_into_ssl()
    logger.debug("System trust store injected")
    server = create_server()
    try:
        logger.info("Running MCP server with streamable HTTP transport")
        server.run(transport="streamable-http")
    except KeyboardInterrupt:
        # Graceful user-initiated shutdown (Ctrl+C) without traceback noise.
        logger.info("Received keyboard interrupt, shutting down")
        return


if __name__ == "__main__":
    main()
