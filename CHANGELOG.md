# Changelog

All notable changes to this project are documented in this file.

This changelog is based on git tags and commit history.

## [0.3.0] - 2026-03-17

### Added

- add `search_datasets` MCP tool powered by CKAN `package_search` with support for query, filters, pagination, sort, and facets
- add shared CKAN utility module `datagovma_mcp.utils.ckan` for action URL building, HTTP fetch, envelope validation, and normalization helpers
- add dedicated search tool tests plus shared test helpers for MCP/client fakes

### Changed

- register `search_datasets` in the server tool registry
- refactor `get_portal_status` to reuse shared CKAN utilities and remove duplicated request/parsing logic
- add argument-level docstring examples in `search_datasets` for `fq`, `sort`, `facet_fields`, and pagination fields

## [0.2.3] - 2026-03-16

### Added

- package the project as an installable Python distribution with a `src/datagovma_mcp` layout
- add `datagovma-mcp` console script entry point via `pyproject.toml`

### Changed

- migrate imports and tests to package-qualified paths (`datagovma_mcp.*`)
- lower supported Python baseline to `>=3.11` and align lint/type config targets
- update README run instructions to use the installed CLI

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
