# Changelog

All notable changes to this project are documented in this file.

This changelog is based on git tags and commit history.

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
