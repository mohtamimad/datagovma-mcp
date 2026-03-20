# datagovma-mcp

MCP server for the Moroccan Open Data portal ([data.gov.ma](https://data.gov.ma)).

`datagovma-mcp` exposes curated MCP tools backed by CKAN Action API endpoints so AI clients can discover datasets, resources, organizations, and groups in a consistent typed shape.

## What this project provides

- Streamable HTTP MCP server built with FastMCP.
- Typed and validated tool inputs/outputs.
- Centralized CKAN envelope validation (`success` checks, JSON checks, timeout handling).
- Test suite covering success and error paths.
- Docker image and Docker Compose setup.

## Implemented MCP tools

| MCP tool | CKAN action | Purpose |
| --- | --- | --- |
| `get_portal_status` | `status_show` | Check portal identity and CKAN version. |
| `search_datasets` | `package_search` | Full-text search with paging and optional facets. |
| `get_dataset` | `package_show` | Fetch one dataset by slug or UUID. |
| `list_datasets` | `package_list` | List dataset names with pagination. |
| `get_resource` | `resource_show` | Fetch one resource and download metadata. |
| `search_resources` | `resource_search` | Search resources using strict `field:value` query format. |
| `list_organizations` | `organization_list` | List organization names with pagination. |
| `get_organization` | `organization_show` | Fetch organization details and optional datasets. |
| `list_groups` | `group_list` | List group names with pagination. |
| `get_group` | `group_show` | Fetch group details and optional datasets. |
| `get_dataset_facets` | `package_search` (`rows=0`) | Aggregate facet buckets (`tags`, `groups`, `organization`). |

## Requirements

- Python `>=3.11`
- [uv](https://docs.astral.sh/uv/) for dependency management
- Docker (optional, for containerized runs)

## Quick start (local)

```bash
uv sync --frozen --group dev
cp .env.example .env
set -a && source .env && set +a
uv run datagovma-mcp
```

Default endpoint:

- MCP: `http://127.0.0.1:8000/mcp`
- Health: `http://127.0.0.1:8000/healthz`

Quick health check:

```bash
curl -fsS http://127.0.0.1:8000/healthz
```

Expected response:

- `200 OK` with body `ok`.

## Run with Docker

```bash
docker compose up --build
```

The service starts on port `8000` by default and exposes `/mcp` and `/healthz`.

## Connect from LLM clients

### Claude Desktop

After the server is running, edit:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

Then add:

```json
{
  "mcpServers": {
    "opengovma": {
      "command": "npx",
      "args": ["mcp-remote", "http://127.0.0.1:8000/mcp"]
    }
  }
}
```

### Claude Code

Add the server with Claude Code CLI:

```bash
claude mcp add --transport http opengovma http://127.0.0.1:8000/mcp
```

### Codex (Desktop app and CLI)

Add the server with Codex CLI:

```bash
codex mcp add opengovma --url http://127.0.0.1:8000/mcp
```

### VS Code (GitHub Copilot MCP)

Create `.vscode/mcp.json` in your workspace (or open your user MCP config via command palette) and add:

```json
{
  "servers": {
    "opengovma": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### Cursor

Add this to `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "opengovma": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## Configuration

Environment variables are loaded by your shell or container runtime.

| Variable | Default | Description |
| --- | --- | --- |
| `MCP_HOST` | `127.0.0.1` | Host interface used by Uvicorn inside the app. |
| `MCP_BIND_HOST` | `0.0.0.0` | Docker Compose helper mapped to `MCP_HOST`. |
| `MCP_PORT` | `8000` | Listening port. |
| `MCP_WORKERS` | `1` | Number of worker processes (`>=1`). |
| `MCP_RELOAD` | `false` | Hot reload mode for development (`true/false`, `1/0`, `yes/no`, `on/off`). |
| `MCP_TIMEOUT_KEEP_ALIVE` | `5` | HTTP keep-alive timeout in seconds (`>=1`). |
| `MCP_LOG_LEVEL` | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `MCP_LOG_FORMAT` | `auto` | One of `auto`, `plain`, `rich`. |

Notes:

- `MCP_RELOAD=true` requires `MCP_WORKERS=1`.
- `MCP_LOG_FORMAT=rich` falls back to plain logs if Rich is unavailable.

## Continuous integration

GitHub Actions workflow: `.github/workflows/ci.yml`

CI runs on pull requests and pushes to `main`/`master` and includes:

- dependency review (PR only)
- lint (`ruff`)
- format check (`ruff format --check`)
- type check (`mypy`)
- tests (`pytest`)
- package build (`uv build`)

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, checks, and PR guidance.

## License

Licensed under the MIT License. See [LICENSE](LICENSE).
