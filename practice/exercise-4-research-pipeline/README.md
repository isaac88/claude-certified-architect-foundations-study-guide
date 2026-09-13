# Exercise 4 — multi-agent research pipeline (Domain 5 lab)

Coordinator plus three spokes over a synthetic corpus, exercising the five
points of the brief in [docs/exercises.md #4](../../docs/exercises.md):
persistent case facts (5.1), explicit context passing with claim–source
mappings (1.3, 5.6), a simulated timeout with partials (5.3), a two-figure
conflict (5.6), and trim-before-append plus a crash-recovery manifest (5.1).

## Files

| File | What it is |
|---|---|
| [pipeline.py](pipeline.py) | `Pipeline`: the coordinator loop (Claude with three tools that *are* the spokes) plus the spoke handlers. Each spoke is a fresh `messages.create` with a structured brief — never the coordinator's history. Ends by writing the log and running six measured checks. |
| [fixtures.py](fixtures.py) | Synthetic corpus — every organisation, figure and URL is invented (`example.org`). Web corpus carries the conflict (3.5 GW end-2022 vs 4.0 GW end-2024). Journal corpus is the flaky source: times out on its first call of a run and on any broad query, returning partials. One local document for the document spoke. |
| [run-log.md](run-log.md) | Generated, committed: checks table, coordinator trace turn by turn, and the synthesis report unedited. |
| [run-manifest.json](run-manifest.json) | Generated, committed: case facts + every full mapping + open gaps, flushed after each spoke. A crashed run resumes from here. |

## Run it

```bash
# from the repo root; ANTHROPIC_API_KEY from the environment or academy/course-c-claude-api/.env
.venv/bin/python practice/exercise-4-research-pipeline/pipeline.py
```

About a minute, ~7 API calls on `claude-opus-5` (override with `PIPELINE_MODEL`).
Progress prints per coordinator turn and per spoke.

## How each brief point is built

1. **Case facts** — `CASE_FACTS` is rendered verbatim into the system prompt
   of every coordinator request (the API is stateless, so every request *is*
   every turn) and into every spoke's system prompt. Nothing ever summarises
   it. Check 1 counts requests that carried the block.
2. **Explicit context passing** — a spoke gets `focus` + numbered sources and
   returns `{source_id, claim, excerpt}`. The harness joins `url`, `title`,
   `date` from the source it cited by id, and downgrades a non-verbatim
   excerpt to the source text. Provenance is attached mechanically; a model
   cannot type a URL into a finding.
3. **Timeout** — `SimulatedTimeout` becomes `status: "error"` with `type`,
   `attempted`, `partials` (already stored as findings) and `alternatives`,
   sent back with `is_error: true`. The coordinator's prompt gives it the
   choice 5.3 describes: retry once (same or narrower query) or proceed.
   A same-query retry closes the gap; a narrower one leaves it for synthesis.
   Check 2 asserts the turn after an error was not `end_turn`.
4. **Conflict** — synthesis is told: adjacent rows, one sentence on what
   differs, never pick, never average. Check 3 asserts both values appear.
5. **Trim + manifest** — the coordinator's tool result is `{id, claim, date}`
   per finding; `url` and `excerpt` never enter its history (check 6 measures
   history size against the full mappings). `run-manifest.json` is rewritten
   after every spoke.

## What the committed run showed

- Turn 1: the coordinator dispatched web search, journal search and the
  document spoke in parallel. The journal call timed out after 1 of 2
  results; the partial was stored as F3.
- Turn 2: it chose the "narrower query" alternative rather than stopping or
  declaring the topic absent. The retry returned two abstracts — one of them
  the same study as F3 (stored again as F7; de-duplication is not in the
  brief, and the coordinator named the duplicate in its closing lines).
- Synthesis put both capacity figures on adjacent rows with dates and a
  scope caveat, and wrote a "Coverage" section naming the EU-level policy
  gap as the thin part. Five URLs cited, all from findings.
- 6/6 checks PASS. The coordinator's query wording varies between runs, so
  the trace differs run to run; the checks are what is stable.
