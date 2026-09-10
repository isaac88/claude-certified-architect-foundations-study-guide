# Exercise 5 — Domain 2 tool contract lab

Working MCP server + client loop that exercises the Domain 2 contracts:
tool descriptions as routing (2.1), structured error categories (2.2),
valid-empty vs access-failure (2.2), MCP registration with `${ENV_VAR}`
(2.4), and `tool_choice` forcing (ties to 1.1). Spec: [docs/exercises.md #5](../../docs/exercises.md).

## Files

| File | What it is |
|---|---|
| [mcp_server.py](mcp_server.py) | FastMCP stdio server (same shape as the course's `mcp-project/mcp_server.py`). Three tools — `get_customer`, `lookup_order`, `process_refund` — over an in-memory dataset. `TOOL_DESCRIPTIONS=vague\|full` switches the description set; all four error categories are returned as structured payloads (`isError`, `errorCategory`, `isRetryable`, `message`, `attempted`). |
| [client_loop.py](client_loop.py) | `MCPClient` (stdio plumbing, course shape) + `SupportAgent`: the loop on `stop_reason == "tool_use"` with the per-category reaction policy — harness retries transients with backoff; validation/business/permission go back to the model as `is_error` results; empty successes go back as plain successes. |
| [experiments.py](experiments.py) | Runs the four experiments against live `claude-opus-5` and writes measured traces to the log. |
| [experiment-log.md](experiment-log.md) | The measured before/after results (generated, committed). |
| [/.mcp.json](../../.mcp.json) | Project-level registration: `${SUPPORT_DESK_API_KEY}` and `${TOOL_DESCRIPTIONS:-full}` expand from the environment — no secret in the file. The server exits at startup if the key expansion is broken, so a bad config fails loud. |

## Run it

```bash
# from the repo root — the key can be any value for this lab, but must exist
export SUPPORT_DESK_API_KEY=dummy
.venv/bin/python practice/exercise-5-tool-contract-lab/client_loop.py     # smoke test
.venv/bin/python practice/exercise-5-tool-contract-lab/experiments.py    # full lab, writes the log
```

`ANTHROPIC_API_KEY` is read from the environment or from
`academy/course-c-claude-api/.env` (same key the course project uses).

## The contracts being exercised

- **Descriptions are the routing layer — but not the only one.** The vague
  pair puts the word "orders" in `get_customer`'s one-liner; the full set
  states purpose, input format with an example, edge behaviour (empty =
  definitive answer), and the boundary with the sibling tool. Measured
  outcome (experiment 1): the misroute did NOT reproduce — distinct tool
  names and input schemas kept routing correct 16/16 even on Haiku — while
  description quality showed up elsewhere: the full `process_refund`
  description let the model pre-empt a doomed over-limit call entirely.
  See the conclusions in [experiment-log.md](experiment-log.md).
- **`errorCategory` names the next move**: transient → retry with backoff
  (in the harness, not the model); validation → fix input, retry; business →
  `isRetryable: false` **plus customer-safe text** the agent relays;
  permission → escalate, never retry with the same credentials.
- **Empty ≠ error.** `customers: []` / `order: null` are successes
  (`isError: false`): the query ran, the answer is "no such record". Marking
  them errors makes the agent retry a lookup that can never succeed;
  marking a timeout as `[]` makes it tell the customer they don't exist.
- **`tool_choice: {"type": "tool", ...}`** forces the first call `auto`
  skips. Two footnotes that matter for the exam: forcing is incompatible
  with extended thinking (thinking must be disabled on the forced request),
  and Fable 5.1 removed forced `tool`/`any` entirely — `auto` + explicit
  prompt instruction is the substitute there.
