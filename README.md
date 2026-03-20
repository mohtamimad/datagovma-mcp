# datagovma-mcp

MCP server for the Moroccan Open Data portal ([data.gov.ma](https://data.gov.ma)).

## Run MCP Server (HTTP Transport)

The server uses the official FastMCP streamable HTTP transport.

```bash
uv run datagovma-mcp
```

By default, FastMCP serves on `http://127.0.0.1:8000/mcp`.

You can override host/port using a local `.env` file:

```bash
cp .env.example .env
set -a && source .env && set +a
```

Environment variables:

- `MCP_HOST` (default: `127.0.0.1`)
- `MCP_PORT` (default: `8000`)
- `MCP_WORKERS` (default: `1`; must be `>= 1`)
- `MCP_RELOAD` (default: `false`; boolean: `true/false`, `1/0`, `yes/no`, `on/off`)
- `MCP_TIMEOUT_KEEP_ALIVE` (default: `5`; seconds, must be `>= 1`)
- `MCP_LOG_LEVEL` (default: `INFO`; one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- `MCP_LOG_FORMAT` (default: `auto`; one of `auto`, `plain`, `rich`)
- `MCP_BIND_HOST` (Docker Compose only; default: `0.0.0.0`; mapped to app `MCP_HOST` inside container)

Notes:

- `MCP_RELOAD=true` requires `MCP_WORKERS=1`.
- HTTP transport is now started via Uvicorn with FastMCP's `streamable_http_app()` factory.
- Liveness endpoint: `GET /healthz` returns `200` with body `ok`.

## API Baseline (validated on 2026-03-08)

- API base URL: `https://data.gov.ma/data/api/3/action`
- Backend: CKAN `2.9.11` (`status_show`)
- Response envelope is CKAN standard:
  - `success` (`true`/`false`)
  - `result` (payload)
  - `help` (doc string URL/text)
- Important: some failures still return HTTP `200`, so tool code must always check `success`.
- Auth model (for non-public actions): `Authorization` or `X-CKAN-API-Key`.

### Observed portal quirks

- Public metadata endpoints are available (`package_*`, `resource_show`, `organization_*`, `group_*`).
- `package_search?rows=0` reports ~`663` datasets at this time.
- No `datastore_active=true` resources were found across current datasets, so DataStore tools should be lower priority.
- `tag_list` currently returns an empty list; tag-like insights are still available via `package_search` facets.
- `resource_search` works with `field:value` queries (example: `name:stat`), but some patterns can be blocked by site WAF and return HTML `Request Rejected`.

## Proposed project structure

```text
datagovma-mcp/
  src/
    datagovma_mcp/
      main.py              # MCP server entrypoint (streamable HTTP)
      tools/
        status.py          # status_show tool implementation
  tests/
    test_status.py
    test_main.py
```

## Tool roadmap (build + test one by one)

1. `get_portal_status`
   - API: `status_show`
   - Why first: validates connectivity and shared response/error handling.
   - Test: assert `ckan_version`, `site_url`, and `extensions` presence.

2. `search_datasets`
   - API: `package_search`
   - Inputs: `q`, `fq`, `rows`, `start`, `sort`, optional `facet_fields`.
   - Test: query returns `count`, `results`, pagination fields.

3. `get_dataset`
   - API: `package_show`
   - Inputs: `id` (name or UUID).
   - Test: response includes core metadata and resources list.

4. `list_datasets`
   - API: `package_list`
   - Inputs: `limit`, `offset`.
   - Test: paging works and names are stable strings.

5. `get_resource`
   - API: `resource_show`
   - Inputs: `id`.
   - Test: format, mimetype, download URL, and package linkage returned.

6. `list_organizations` + `get_organization`
   - APIs: `organization_list`, `organization_show`.
   - Test: basic listing, details with optional dataset inclusion.

7. `list_groups` + `get_group`
   - APIs: `group_list`, `group_show`.
   - Test: listing plus group detail with package count.

8. `get_dataset_facets` (practical replacement for `tag_list`)
   - API: `package_search` with `rows=0` + `facet.field`.
   - Test: returns facet buckets for `tags`, `groups`, `organization`.

9. `search_resources` (phase 2, guarded)
   - API: `resource_search`
   - Caveat: apply strict validation (`field:value` only) and graceful fallback on WAF rejection.

10. DataStore tools (phase 3, optional)
   - APIs: `datastore_search`, `datastore_info`
   - Condition: enable once the portal exposes `datastore_active` resources.

## Implementation order

Start with `get_portal_status` and `search_datasets`, then continue in roadmap order.
Each tool should ship with:

- input schema validation,
- CKAN envelope validation (`success` + `error` mapping),
- one unit test for success,
- one unit test for API error path,
- one live smoke test (optional flag) against `data.gov.ma`.

## License

This project is open-sourced under the MIT License.

- You can use, modify, and distribute this software, including for commercial use.
- You must keep the copyright and license notice in copies/substantial portions.
- The software is provided "as is", without warranty.

See [LICENSE](LICENSE) for the full text.
