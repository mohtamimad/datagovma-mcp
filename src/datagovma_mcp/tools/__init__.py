"""Tool modules for the data.gov.ma MCP server."""

import logging

from mcp.server.fastmcp import FastMCP

from datagovma_mcp.tools.get_dataset import register_get_dataset_tool
from datagovma_mcp.tools.get_organization import register_get_organization_tool
from datagovma_mcp.tools.get_resource import register_get_resource_tool
from datagovma_mcp.tools.list_datasets import register_list_datasets_tool
from datagovma_mcp.tools.list_groups import register_list_groups_tool
from datagovma_mcp.tools.list_organizations import register_list_organizations_tool
from datagovma_mcp.tools.search_datasets import register_search_datasets_tool
from datagovma_mcp.tools.status import register_status_tool

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools."""

    logger.info("Registering MCP tools")
    registrars = (
        register_status_tool,
        register_search_datasets_tool,
        register_get_dataset_tool,
        register_list_datasets_tool,
        register_get_resource_tool,
        register_list_organizations_tool,
        register_get_organization_tool,
        register_list_groups_tool,
    )
    for register_tool in registrars:
        register_tool(mcp)
    logger.info("Registered %s MCP tools", len(registrars))
