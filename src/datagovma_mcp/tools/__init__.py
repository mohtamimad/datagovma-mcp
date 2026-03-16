"""Tool modules for the data.gov.ma MCP server."""

from mcp.server.fastmcp import FastMCP

from datagovma_mcp.tools.status import register_status_tool


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools."""

    register_status_tool(mcp)
