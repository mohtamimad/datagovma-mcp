"""Tool modules for the data.gov.ma MCP server."""

from mcp.server.fastmcp import FastMCP

from datagovma_mcp.tools.get_dataset import register_get_dataset_tool
from datagovma_mcp.tools.search_datasets import register_search_datasets_tool
from datagovma_mcp.tools.status import register_status_tool


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools."""

    register_status_tool(mcp)
    register_search_datasets_tool(mcp)
    register_get_dataset_tool(mcp)
