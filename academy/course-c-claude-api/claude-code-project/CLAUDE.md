# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project overview

Document Tools — a Python package of document-conversion tools exposed through an
MCP server (FastMCP, `mcp[cli]==1.8.0`). `main.py` creates the server and registers
tools; the tool implementations live in `tools/` as plain Python functions.

## Commands

```bash
# Install (uv-managed venv from the shipped lockfile)
uv sync

# Start the MCP server (stdio)
uv run main.py

# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/test_document.py -k <name>
```

## Architecture

- `main.py` — creates `FastMCP("docs")` and registers tools with `mcp.tool()(fn)`.
  Every new tool must be registered here or the server never exposes it.
- `tools/math.py`, `tools/document.py` — tool implementations. Ordinary functions;
  the MCP schema is generated from type hints + pydantic `Field` descriptions.
- `tools/document.py` uses `markitdown` for binary → markdown conversion
  (docx and pdf extras installed).
- `tests/` mirrors `tools/`; fixtures in `tests/fixtures/` (a real docx and pdf).

## Coding guidelines

Tool descriptions should:

- Begin with a one-line summary
- Provide detailed explanation of functionality
- Explain when to use (and not use) the tool
- Include usage examples with expected input/output

Every tool parameter takes a pydantic `Field(description=...)`. Follow the
existing `add` tool in `tools/math.py` as the template.
