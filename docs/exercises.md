# Hands-on exercises

These four builds match the public preparation guidance. You do not need to commit code here; keep experiments in a sibling folder if you prefer.

## 1. Multi-tool support agent

**Domains:** 1, 2, 5

1. Agent SDK app with at least three tools (`get_customer`, `lookup_order`, `process_refund`).
2. Loop on `stop_reason == "tool_use"`; stop on `"end_turn"`.
3. `PreToolUse` or a prerequisite gate: no refund until a verified customer ID exists.
4. `PostToolUse` hook: block or redirect refunds over a threshold; normalise status codes.
5. Structured tool errors: `isError`, `errorCategory`, `isRetryable`.
6. Explicit escalation criteria; a self-contained handoff summary.

## 2. Claude Code team workflow (Domain 3 lab)

**Domains:** 3, 2

1. Project-level `.claude/CLAUDE.md` (team standards) **and** a directory-level `CLAUDE.md` in one package. Keep personal notes only in `~/.claude/CLAUDE.md` so you can see the 3.1 trap.
2. `.claude/rules/` with glob `paths` for **test files** and **API files** (not one always-on blob).
3. Project slash command `/review` in `.claude/commands/`.
4. A skill with `context: fork` and `allowed-tools` (read-only if it is exploratory). Optional: a **personal** skill in `~/.claude/skills/` with a different name.
5. CI script: `claude -p` with `--output-format json` (and `--json-schema` if you have a schema). Prove that omitting `-p` is what hangs a job.
6. One MCP server in `.mcp.json` using `${ENV_VAR}` (from Domain 2).

## 3. Structured extraction pipeline (Domain 4 lab)

**Domains:** 4, 5

1. Extraction **tool** with JSON Schema: required, **optional/nullable**, enums including **`other`** (and `unclear` if you classify).
2. `tool_use` + `tool_choice` (`"any"` or forced name). Prove “respond only with JSON” is not the guarantee.
3. Validation-retry: original document + failed JSON + **field-level** errors. Include one **unfixable** case (field absent) and confirm you **stop** rather than invent.
4. `stated_total` / `calculated_total` or `conflict_detected`; optional `detected_pattern` on review findings.
5. **10 documents**, mixed layouts. Add 2–4 few-shot examples covering those layouts; compare extraction quality before vs after.
6. Optional: Message Batches for a non-blocking bulk run; keep a “developer waiting” path on the synchronous API.

## 4. Multi-agent research pipeline (Domain 5 lab)

**Domains:** 1, 2, 5

Coordinator plus **at least two** subagents (search + synthesis is enough; a third document spoke is better).

1. **Persistent case-facts** (or run-facts) block injected every coordinator turn — query, constraints, IDs. Never summarise that block.
2. Explicit context passing — never the full coordinator history. Structured claim–source mappings (URL, title, excerpt, **date**).
3. Simulate a **timeout**: spoke returns structured error (type, attempted query, **partials**, alternatives). Coordinator does not treat it as empty success and does not kill the job. Synthesis **annotates the coverage gap**.
4. **Conflict fixture**: two sources, two numbers, different dates. Synthesis keeps **both** with attribution (table for the figures).
5. Optional: scratchpad/manifest for crash recovery; trim verbose tool payloads before append.

## 5. Domain 2 tool contract lab

**Domains:** 2 (and 1.1 if you wire a tiny loop)

Keep this in a sibling folder if you do not want experiment code in the study-guide repo.

1. Create **three** MCP tools. Make **one pair intentionally ambiguous** (one-line overlapping descriptions), then **fix** that pair with full descriptions: purpose, inputs, examples, edges, boundaries.
2. Implement error responses covering all **four** categories: transient, validation, business (`isRetryable: false` + customer-safe text), permission. Include one **valid empty** success (not an error) and one **access failure** that is an error — prove the agent treats them differently.
3. Register the server in project `.mcp.json` with `${ENV_VAR}` expansion. No secrets in the file.
4. Force the first step with `tool_choice: {"type": "tool", "name": "..."}` (for example `get_customer` before anything else). Confirm `"auto"` no longer skips it.
5. Optional: give a “synthesis” role a **scoped** `verify_fact` and refuse it `fetch_url`.
