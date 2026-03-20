# Contributing to datagovma-mcp

Thanks for your interest in contributing.

## Development setup

1. Fork and clone the repository.
2. Install dependencies with uv.

```bash
uv sync --frozen --group dev
```

3. Install pre-commit hooks.

```bash
uv run pre-commit install
```

## Required checks

Run all configured hooks before opening a pull request:

```bash
uv run pre-commit run --all-files
```

## Coding guidelines

- Keep changes focused and small when possible.
- Preserve type hints and explicit validation patterns used in existing tools.
- Add or update tests for both success and error paths when behavior changes.
- Prefer updating docs when introducing new tools, flags, or behavior.

## Commit message convention

Use Conventional Commit style with a scope when possible, for example:

- `feat(dataset): add xyz`
- `fix(api): handle xyz`
- `chore(ci): update workflow`
- `docs(readme): clarify setup`

## Pull request checklist

Before requesting review, ensure:

- all checks pass locally;
- CI is green;
- tests/docs are updated for your change;
- PR description explains what changed and why.

## Reporting issues

When opening an issue, include:

- clear steps to reproduce;
- expected vs actual behavior;
- environment details (OS, Python version, command used);
- relevant logs or tracebacks.

For sensitive security issues, avoid posting exploit details publicly in an issue.
