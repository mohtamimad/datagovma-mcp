# Changelog

All notable changes to this project are documented in this file.

This changelog is based on git tags and commit history.

## [0.11.0] - 2026-03-19

### Added

- add `list_groups` MCP tool powered by CKAN `group_list` with `limit`/`offset` paging and normalized string-name results (`ecfbc9f`)
- add dedicated `list_groups` tests for success path, API error path, input validation, and MCP registration wiring (`ecfbc9f`)

### Changed

- register `list_groups` in the server tool registry (`ecfbc9f`)
- standardize counting field names across MCP tools to use explicit `*_count` naming (for example `total_count`, `dataset_count`, `organization_count`, and `group_count`) (`d4b7097`)

### Chore

- bump package version to `0.11.0`

## [0.10.0] - 2026-03-19

### Added

- add `get_organization` MCP tool powered by CKAN `organization_show` with optional `include_datasets` expansion and normalized organization metadata (`421758c`)
- add dedicated `get_organization` tests for success path, API error path, input validation, and MCP registration wiring (`421758c`)

### Changed

- register `get_organization` in the server tool registry (`421758c`)

### Chore

- bump package version to `0.10.0`

## [0.9.0] - 2026-03-19

### Added

- add `list_organizations` MCP tool powered by CKAN `organization_list` with `limit`/`offset` paging and normalized string-name results (`9f23ba4`)
- add dedicated `list_organizations` tests for success path, API error path, input validation, and MCP registration wiring (`9f23ba4`)

### Changed

- register `list_organizations` in the server tool registry (`9f23ba4`)
- deduplicate CKAN list-response normalization by adding shared `as_required_str_list` helper and reusing it in dataset/organization listing tools (`9f23ba4`)

### Chore

- bump package version to `0.9.0`

## [0.8.1] - 2026-03-19

### Changed

- refactor CKAN action fetch helpers to centralize async client resolution and remove duplicated tool-level `httpx.AsyncClient` wiring (`3387291`)
- move optional string trimming/blank-collapse logic into shared normalizers for reuse across tools (`3387291`)
- simplify server construction to use host/port config directly while keeping Uvicorn runtime settings in startup flow (`3387291`)

### Chore

- bump package version to `0.8.1`

## [0.8.0] - 2026-03-19

### Added

- add Uvicorn runtime configuration via environment variables: `MCP_WORKERS`, `MCP_RELOAD`, and `MCP_TIMEOUT_KEEP_ALIVE` (`d445f32`)
- add startup/config test coverage for Uvicorn factory mode and validation rules (including `reload` + workers compatibility) (`d445f32`)

### Changed

- run HTTP transport through explicit `uvicorn.run(..., factory=True)` with FastMCP `streamable_http_app()` (`d445f32`)
- standardize server config parsing helpers for host/int/bool normalization and validation (`d445f32`)

### Docs

- document new Uvicorn-related environment variables in README and `.env.example` (`d445f32`)

### Chore

- bump package version to `0.8.0`

## [0.7.0] - 2026-03-19

### Added

- add `get_resource` MCP tool powered by CKAN `resource_show` with normalized resource metadata fields including format, mimetype, size, and package linkage (`16a48ac`)
- add dedicated `get_resource` tests for success path, API error path, input validation, and MCP registration wiring (`16a48ac`)

### Changed

- register `get_resource` in the server tool registry (`16a48ac`)
- reuse shared input/output helpers by adding `validate_non_empty_str` and `as_optional_int`, then applying them across dataset/resource tool paths (`16a48ac`)

### Chore

- bump package version to `0.7.0`

## [0.6.0] - 2026-03-18

### Added

- add `list_datasets` MCP tool powered by CKAN `package_list` with `limit`/`offset` paging and normalized string-name results (`e680cb6`)
- add dedicated `list_datasets` tests for success path, API error path, input validation, and MCP registration wiring (`e680cb6`)
- add shared `utils/normalizers.py` and `utils/validators.py` modules for reusable normalization and validation helpers (`e680cb6`)

### Changed

- register `list_datasets` in the server tool registry (`e680cb6`)
- split generic helpers out of `utils.ckan` and keep CKAN transport/envelope handling centralized there (`e680cb6`)
- add `fetch_ckan_action_result` to support CKAN actions with non-object `result` payloads while preserving object validation in `fetch_ckan_result` (`e680cb6`)

## [0.5.0] - 2026-03-18

### Added

- add project-wide structured logging with environment-driven level configuration across server components (`920672b`)
- add logging test coverage for configuration behavior and startup integration (`920672b`)

### Changed

- centralize Uvicorn logger propagation and access log level handling in shared logging configuration (`4aac67d`)
- centralize output format resolution (`auto`, `plain`, `rich`) and support `MCP_LOG_FORMAT` configuration (`4aac67d`)

### Docs

- improve MCP tool docstrings to explicitly describe Morocco Open Data Government usage (`fd5b592`)
- add clarifying inline comments for CKAN envelope and facet encoding behavior (`f5cea53`)

### Chore

- bump package version to `0.5.0`

## [0.4.0] - 2026-03-17

### Added

- add `get_dataset` MCP tool powered by CKAN `package_show` with normalized core metadata, organization, tags/groups, and resources (`8b4c171`)
- add dedicated `get_dataset` tool tests for success path, API error path, input validation, and MCP registration wiring (`8b4c171`)

### Changed

- register `get_dataset` in the server tool registry (`8b4c171`)

### Chore

- bump package version to `0.4.0`

## [0.3.0] - 2026-03-17

### Added

- add `search_datasets` MCP tool powered by CKAN `package_search` with support for query, filters, pagination, sort, and facets (`01714cb`)
- add shared CKAN utility module `datagovma_mcp.utils.ckan` for action URL building, HTTP fetch, envelope validation, and normalization helpers (`01714cb`)
- add dedicated search tool tests plus shared test helpers for MCP/client fakes (`01714cb`)

### Changed

- register `search_datasets` in the server tool registry (`01714cb`)
- refactor `get_portal_status` to reuse shared CKAN utilities and remove duplicated request/parsing logic (`01714cb`)
- add argument-level docstring examples in `search_datasets` for `fq`, `sort`, `facet_fields`, and pagination fields (`01714cb`)

## [0.2.3] - 2026-03-16

### Added

- package the project as an installable Python distribution with a `src/datagovma_mcp` layout (`ce4d556`)
- add `datagovma-mcp` console script entry point via `pyproject.toml` (`ce4d556`)

### Changed

- migrate imports and tests to package-qualified paths `datagovma_mcp.*` (`ce4d556`)
- lower supported Python baseline to `>=3.11` and align lint/type config targets (`ce4d556`)
- update README run instructions to use the installed CLI (`ce4d556`)

## [0.2.2] - 2026-03-09

### Chore

- add MIT license and project license metadata (`e817240`)
- ignore local uv cache directory `.uv-cache/` in git

## [0.2.1] - 2026-03-09

### Docs

- clarify status tool docstrings (`adf959d`)

## [0.2.0] - 2026-03-08

### Added

- set up streamable HTTP server and MCP tool registration (`dbf77c6`)
- enable stateless HTTP transport mode (`3b257df`)

### Changed

- make status tool async with `httpx` (`def68a8`)
- extract env config utility and improve server shutdown flow (`fad28f2`)

### Chore

- ignore pytest, ruff, and mypy cache files in git (`10f821d`)

## [0.1.0] - 2026-03-08

### Added

- bootstrap project tooling and quality gates (`13cbe44`)
- add CKAN status tool and CLI (`f73d01e`)
- add pytest coverage for status tool (`0f2c132`)

### Docs

- add API and tool implementation roadmap (`e7a94c1`)
