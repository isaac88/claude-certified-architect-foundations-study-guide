---
paths:
  - "**/mcp_server.py"
  - "**/mcp_client.py"
  - "**/client_loop.py"
  - "**/pipeline.py"
---

# Files on the model or tool boundary

- A tool never raises across the boundary; it returns a structured payload and the harness mirrors the payload's error flag into `is_error`. Two shapes are in use: MCP tools (`mcp_server.py`, `client_loop.py`) return `{isError, errorCategory (transient|validation|business|permission), isRetryable, message, attempted}`; pipeline spokes (`pipeline.py`) return `{status: ok|empty|error, error: {type, attempted, partials, alternatives}}`. Keep to the shape the file already uses.
- An empty successful result (`[]`, `null`) is a definitive answer, not an error: `is_error` stays unset and nothing retries it.
- The loop runs on `stop_reason == "tool_use"`. Every `tool_use` block of one assistant turn is answered in ONE user message. Append `response.content` (the block list), never a string.
- Transients: the harness may retry with backoff before the model sees the failure (`client_loop.py`), or the spoke may propagate a rich error with partials and let the coordinator choose retry-or-proceed (`pipeline.py`) — both are valid; what is never valid is a silent `[]` success or an uncaught exception. Validation/business/permission go back to the model as `is_error` results, never retried by the harness.
- Trim tool payloads before appending them to history; keep the full payload in the harness or a manifest.
- A case-facts block, when the script has one, is injected verbatim on every request and never summarised.
- The model id is one constant at the top of the file; long runs print progress per turn and per spoke.
