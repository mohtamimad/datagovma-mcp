"""MCP server entrypoint using streamable HTTP transport."""

from __future__ import annotations

import logging

import truststore
import uvicorn
from mcp.server.fastmcp import FastMCP

from datagovma_mcp.tools import register_tools
from datagovma_mcp.utils.logging_config import configure_logging, configure_uvicorn_logging
from datagovma_mcp.utils.server_config import get_uvicorn_server_config

logger = logging.getLogger(__name__)


def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance."""

    server_config = get_uvicorn_server_config()
    logger.info("Creating MCP server on %s:%s", server_config.host, server_config.port)
    mcp = FastMCP(
        "data.gov.ma MCP server",
        host=server_config.host,
        port=server_config.port,
        stateless_http=True,
    )
    register_tools(mcp)
    logger.debug("MCP tools registered")
    return mcp


def create_http_app():
    """Create the streamable HTTP ASGI app for Uvicorn factory startup."""

    # Ensure worker processes trust the system certificate store for outbound HTTPS.
    truststore.inject_into_ssl()
    logger.debug("System trust store injected")
    server = create_server()
    return server.streamable_http_app()


def main() -> None:
    log_level = configure_logging()
    configure_uvicorn_logging()
    server_config = get_uvicorn_server_config()
    logger.info("Starting data.gov.ma MCP server with log level %s", log_level)
    try:
        logger.info(
            "Running MCP server via uvicorn host=%s port=%s workers=%s reload=%s",
            server_config.host,
            server_config.port,
            server_config.workers,
            server_config.reload,
        )
        uvicorn.run(
            "datagovma_mcp.main:create_http_app",
            factory=True,
            host=server_config.host,
            port=server_config.port,
            workers=server_config.workers,
            reload=server_config.reload,
            timeout_keep_alive=server_config.timeout_keep_alive,
            log_level=log_level.lower(),
        )
    except KeyboardInterrupt:
        # Graceful user-initiated shutdown (Ctrl+C) without traceback noise.
        logger.info("Received keyboard interrupt, shutting down")
        return


if __name__ == "__main__":
    main()
