"""Multi-agent research pipeline — practice exercise 4 (Domain 5 lab).

One coordinator, three spokes, and the five things the brief asks for:

1. CASE FACTS (5.1) — a verbatim block in the system prompt of EVERY
   coordinator request (the API is stateless, so "every turn" means every
   request) and copied into every spoke brief. Never summarised.
2. EXPLICIT CONTEXT PASSING (1.3 / 5.6) — each spoke is a fresh
   messages.create with a structured brief. It never sees the coordinator's
   history. Findings travel as claim-source mappings: claim, url, title,
   excerpt, date. The harness attaches url/title/date from the source the
   spoke cites by id, so provenance is joined mechanically, not typed by a
   model.
3. TIMEOUT (5.3) — the journal corpus times out on its first call of a run
   (transient) and on any broad query (after two abstracts). The spoke
   returns status=error with type, attempted, partials and alternatives.
   Partials are stored as findings. The COORDINATOR decides: retry the same
   or a narrower query, or proceed; it must neither treat it as "no results"
   nor stop the job. Synthesis annotates whatever gap is left.
4. CONFLICT (5.6) — two capacity figures, two dates. Synthesis tables both.
5. TRIM + MANIFEST (5.1, optional in the brief) — the coordinator's history
   only ever receives ids + one-line claims; full mappings live in the
   harness and are flushed to run-manifest.json after every spoke, so a
   crashed run can be resumed from the manifest instead of from scratch.

Run it and read run-log.md: the report, the coordinator trace, and five
measured checks.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

from fixtures import CONFLICT_FIGURES, DOCUMENTS, SimulatedTimeout, search

HERE = Path(__file__).parent
REPO_ROOT = HERE.parents[1]
# Same key the course project and exercise 5 use; load_dotenv never overrides
# an already-exported variable.
load_dotenv(REPO_ROOT / "academy" / "course-c-claude-api" / ".env")

MODEL = os.environ.get("PIPELINE_MODEL", "claude-opus-5")
MANIFEST = HERE / "run-manifest.json"
RUN_LOG = HERE / "run-log.md"

CASE_FACTS = {
    "run_id": "RUN-2026-09-13-geo",
    "question": (
        "What is the current state of geothermal energy in Europe: installed "
        "electricity capacity, recent growth, and the policy direction?"
    ),
    "region": "Europe",
    "period": "publications dated 2022 to 2025 only",
    "output": "Markdown report; key findings first; every figure in a table with source and date",
    "conflict_policy": "two sources disagree on a figure -> show both with dates; never pick one, never average",
    "documents": ", ".join(DOCUMENTS),
}


def case_facts_block() -> str:
    lines = "\n".join(f"- {k}: {v}" for k, v in CASE_FACTS.items())
    return f"## CASE FACTS (verbatim on every turn; never summarise)\n{lines}"


COORDINATOR_SYSTEM = """You are the coordinator of a research pipeline. You do not \
research anything yourself: you dispatch spokes, keep track of coverage, and \
finish with one synthesis call.

Plan, in order:
1. search_spoke on corpus "web" for the installed capacity and growth figures.
2. search_spoke on corpus "journal" for the policy direction.
3. document_spoke for every document id listed in the case facts.
4. synthesis_spoke once, with a section outline. Then reply with three lines: \
what was covered, what is thin and why, and how many findings were gathered.

Spoke results carry a status:
- "ok": the findings are stored; the result lists their ids and one-line claims.
- "empty": the corpus was reached and holds nothing on that query. That is the \
answer. Do not retry the same query; move on.
- "error": the source failed. The `partials` were REAL findings gathered before \
the failure and are already stored; they are not nothing. Choose ONE: retry once \
using one of the listed `alternatives` (a narrower query is usually right), or \
proceed. Never abandon the job and never report the topic as absent.

{case_facts}
"""

COORDINATOR_TOOLS = [
    {
        "name": "search_spoke",
        "description": (
            "Run the search spoke: one query against one corpus. Returns "
            "status ok|empty|error. On ok the new findings are listed by id "
            "with a one-line claim. On error you get type, attempted, "
            "partials (findings gathered before the failure, already stored) "
            "and alternatives."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "corpus": {"type": "string", "enum": ["web", "journal"]},
                "focus": {
                    "type": "string",
                    "description": "One line: what this search must establish. Becomes the spoke's brief.",
                },
            },
            "required": ["query", "corpus", "focus"],
        },
    },
    {
        "name": "document_spoke",
        "description": "Read one local document from the case facts list and extract its claims as findings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "enum": list(DOCUMENTS)},
                "focus": {"type": "string"},
            },
            "required": ["document_id", "focus"],
        },
    },
    {
        "name": "synthesis_spoke",
        "description": (
            "Write the final report from every stored finding plus the recorded "
            "coverage gaps. Call it once, last."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"outline": {"type": "array", "items": {"type": "string"}}},
            "required": ["outline"],
        },
    },
]

EXTRACTION_SYSTEM = """You are the claim-extraction spoke of a research pipeline. \
You receive a brief and numbered sources. Return ONLY JSON:
{"findings": [{"source_id": "...", "claim": "...", "excerpt": "..."}]}
Rules: one finding per relevant source (a long document may yield up to three); \
`claim` is one sentence in your words that keeps every number, unit and date \
exactly as the source states it; `excerpt` is a VERBATIM substring of that \
source's text that supports the claim. Do not merge sources. Do not add \
knowledge that is not in the sources. Skip sources irrelevant to the focus.

{case_facts}
"""

SYNTHESIS_SYSTEM = """You are the synthesis spoke. You receive case facts, a list of \
findings (claim, url, title, excerpt, date) and a list of coverage gaps. Write \
the report in Markdown:

1. "## Key findings" FIRST: 3-5 bullets, the numbers included.
2. One "## <section>" per outline entry, prose, each claim followed by \
[title, date].
3. "## Figures": a table with columns Metric | Value | Source | Date, one row \
per numeric claim. When two findings give different values for the same \
metric, put them on adjacent rows and add one sentence below the table on \
what differs (dates, scope) — never pick one, never average.
4. "## Coverage": one bullet per gap, saying which section is thin and why, \
in plain words; if there are no gaps, say so.
5. "## Sources": every finding's title — url (date). Cite nothing that is not \
in the findings list.

{case_facts}
"""


def _json_from_text(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return json.loads(text)


def _text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


class Pipeline:
    def __init__(self, model: str = MODEL):
        self.client = Anthropic()
        self.model = model
        self.findings: list[dict] = []     # full claim-source mappings (harness-owned)
        self.gaps: list[dict] = []         # coverage gaps for synthesis
        self.trace: list[dict] = []        # coordinator turn log for run-log.md
        self.requests_with_case_facts = 0
        self.coordinator_requests = 0
        self.report = ""

    # -- spokes ---------------------------------------------------------------

    def _extract(self, brief: str, sources: list[dict], text_key: str) -> list[dict]:
        """One fresh Claude call: sources -> findings. Provenance is joined here
        by source_id; a non-verbatim excerpt falls back to the source text."""
        numbered = "\n\n".join(
            f"[{s['id']}] {s['title']} ({s['date']})\n{s[text_key]}" for s in sources
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=EXTRACTION_SYSTEM.replace("{case_facts}", case_facts_block()),
            messages=[{"role": "user", "content": f"BRIEF: {brief}\n\nSOURCES:\n{numbered}"}],
        )
        by_id = {s["id"]: s for s in sources}
        out = []
        for f in _json_from_text(_text(response)).get("findings", []):
            src = by_id.get(f.get("source_id"))
            if src is None:
                continue
            excerpt = f.get("excerpt", "")
            verbatim = excerpt and excerpt in src[text_key]
            out.append(
                {
                    "id": f"F{len(self.findings) + len(out) + 1}",
                    "claim": f.get("claim", ""),
                    "url": src["url"],
                    "title": src["title"],
                    "excerpt": excerpt if verbatim else src[text_key][:240],
                    "excerpt_verbatim": bool(verbatim),
                    "date": src["date"],
                    "source_id": src["id"],
                }
            )
        return out

    def _store(self, new: list[dict]) -> list[dict]:
        self.findings.extend(new)
        self._flush_manifest()
        # what the coordinator gets: ids + claims + dates. No url, no excerpt.
        return [{"id": f["id"], "claim": f["claim"], "date": f["date"]} for f in new]

    def search_spoke(self, query: str, corpus: str, focus: str) -> dict:
        print(f"    [search spoke] corpus={corpus} query={query!r}")
        try:
            hits = search(query, corpus)
        except SimulatedTimeout as e:
            print(f"    [search spoke] TIMEOUT after {len(e.partials)} of {e.matched} results -> partials + structured error")
            partial_findings = self._extract(focus, e.partials, "excerpt") if e.partials else []
            trimmed = self._store(partial_findings)
            gap = {
                "section": focus,
                "query": query,
                "reason": f"journal search {query!r} timed out after {len(e.partials)} of {e.matched} results",
            }
            self.gaps.append(gap)
            self._flush_manifest()
            return {
                "status": "error",
                "error": {
                    "type": "timeout",
                    "attempted": {"query": query, "corpus": corpus},
                    "partials": trimmed,
                    "alternatives": [
                        "retry the same query once: this was a timeout, not an empty result",
                        "retry with a narrower query on one sub-topic (permitting, subsidies, risk insurance, EU strategy)",
                        "search corpus 'web' for the same focus",
                        "proceed; the gap will be annotated in the report",
                    ],
                },
            }
        if not hits:
            print("    [search spoke] 0 hits -> valid empty (reached the corpus, nothing there)")
            return {"status": "empty", "attempted": {"query": query, "corpus": corpus}}
        print(f"    [search spoke] {len(hits)} hits -> extracting claims")
        trimmed = self._store(self._extract(focus, hits, "excerpt"))
        # a successful retry of the SAME query recovers the gap fully; a
        # narrower retry covers a sub-topic and leaves the broad gap annotated
        self.gaps = [g for g in self.gaps if g["query"] != query]
        self._flush_manifest()
        return {"status": "ok", "new_findings": trimmed}

    def document_spoke(self, document_id: str, focus: str) -> dict:
        print(f"    [document spoke] {document_id}")
        doc = {"id": document_id, **DOCUMENTS[document_id]}
        trimmed = self._store(self._extract(focus, [doc], "text"))
        return {"status": "ok" if trimmed else "empty", "new_findings": trimmed}

    def synthesis_spoke(self, outline: list[str]) -> dict:
        print(f"    [synthesis spoke] {len(self.findings)} findings, {len(self.gaps)} gaps, outline={outline}")
        payload = {
            "outline": outline,
            "findings": [
                {k: f[k] for k in ("id", "claim", "url", "title", "excerpt", "date")}
                for f in self.findings
            ],
            "coverage_gaps": self.gaps,
        }
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=SYNTHESIS_SYSTEM.replace("{case_facts}", case_facts_block()),
            messages=[{"role": "user", "content": json.dumps(payload, indent=1)}],
        )
        self.report = _text(response)
        return {"status": "ok", "report_chars": len(self.report), "sections": re.findall(r"^## (.+)$", self.report, re.M)}

    # -- coordinator ----------------------------------------------------------

    def run(self, max_turns: int = 12) -> None:
        system = COORDINATOR_SYSTEM.replace("{case_facts}", case_facts_block())
        messages: list[dict] = [{"role": "user", "content": f"Start run {CASE_FACTS['run_id']}."}]
        last_status: list[str] = []
        for turn in range(1, max_turns + 1):
            self.coordinator_requests += 1
            if case_facts_block() in system:
                self.requests_with_case_facts += 1
            t0 = time.time()
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system,
                tools=COORDINATOR_TOOLS,
                messages=messages,
            )
            calls = [b for b in response.content if b.type == "tool_use"]
            print(f"[coord turn {turn}] stop={response.stop_reason} tools={[c.name for c in calls]} ({time.time() - t0:.1f}s)")
            self.trace.append(
                {
                    "turn": turn,
                    "after_status": ",".join(last_status) or None,
                    "action": [f"{c.name}({json.dumps(dict(c.input))})" for c in calls] or ["end_turn"],
                }
            )
            if response.stop_reason != "tool_use":
                self.final_text = _text(response)
                break
            messages.append({"role": "assistant", "content": response.content})
            results = []
            last_status = []
            for c in calls:
                handler = getattr(self, c.name)
                payload = handler(**dict(c.input))
                last_status.append(payload["status"])
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": c.id,
                        "content": json.dumps(payload),
                        "is_error": payload["status"] == "error",
                    }
                )
            messages.append({"role": "user", "content": results})
        else:
            self.final_text = "(max_turns reached)"
        self.coordinator_messages = messages

    # -- persistence + checks -------------------------------------------------

    def _flush_manifest(self) -> None:
        MANIFEST.write_text(
            json.dumps({"case_facts": CASE_FACTS, "findings": self.findings, "gaps": self.gaps}, indent=1)
        )

    def checks(self) -> list[tuple[str, bool, str]]:
        history = json.dumps(
            self.coordinator_messages,
            default=lambda o: o.model_dump() if hasattr(o, "model_dump") else str(o),
        )
        urls_in_report = set(re.findall(r"https?://\S+|local://[\w-]+", self.report))
        known_urls = {f["url"] for f in self.findings}
        timeout_turns = [t for t in self.trace if "error" in (t["after_status"] or "")]
        full_mappings = json.dumps(self.findings)
        leaked = '"excerpt"' in history or any(f["url"] in history for f in self.findings)
        return [
            (
                "case facts in every coordinator request",
                self.requests_with_case_facts == self.coordinator_requests,
                f"{self.requests_with_case_facts}/{self.coordinator_requests}",
            ),
            (
                "timeout did not end the job",
                bool(timeout_turns) and all(t["action"] != ["end_turn"] for t in timeout_turns),
                "; ".join(", ".join(t["action"]) for t in timeout_turns) or "no timeout occurred",
            ),
            (
                "both conflicting figures in the report",
                all(v.split()[0] in self.report for v in CONFLICT_FIGURES),
                " and ".join(CONFLICT_FIGURES),
            ),
            (
                "coverage gap annotated (or closed by a retry)",
                (not self.gaps) or bool(re.search(r"timed out|limited|partial|thin|gap", self.report, re.I)),
                f"{len(self.gaps)} open gap(s)",
            ),
            (
                "every URL in the report came from a finding",
                urls_in_report <= known_urls,
                f"{len(urls_in_report)} cited, {len(urls_in_report - known_urls)} unknown",
            ),
            (
                "coordinator history holds no excerpt or URL fields",
                not leaked,
                f"history {len(history):,} chars; full mappings {len(full_mappings):,} chars, kept in the harness and manifest",
            ),
        ]

    def write_log(self) -> None:
        checks = self.checks()
        lines = [
            f"# Exercise 4 run log — {CASE_FACTS['run_id']} ({MODEL})",
            "",
            "Generated by `pipeline.py`. Corpus is synthetic (see fixtures.py); the run is live.",
            "",
            "## Checks",
            "",
            "| Check | Result | Evidence |",
            "|---|---|---|",
            *[f"| {name} | {'PASS' if ok else 'FAIL'} | {ev} |" for name, ok, ev in checks],
            "",
            "## Coordinator trace",
            "",
            "| Turn | After spoke status | Action |",
            "|---|---|---|",
            *[f"| {t['turn']} | {t['after_status'] or '—'} | `{'; '.join(t['action'])}` |" for t in self.trace],
            "",
            "Coordinator's closing lines:",
            "",
            *[f"> {l}" for l in self.final_text.strip().splitlines()],
            "",
            f"Findings stored: {len(self.findings)} "
            f"({sum(f['excerpt_verbatim'] for f in self.findings)} with verbatim excerpts). "
            f"Open gaps at synthesis: {len(self.gaps)}.",
            "",
            "## Report (synthesis spoke output, unedited)",
            "",
            self.report.strip(),
            "",
        ]
        RUN_LOG.write_text("\n".join(lines))
        for name, ok, ev in checks:
            print(f"  {'PASS' if ok else 'FAIL'}  {name} — {ev}")
        print(f"\nwrote {RUN_LOG.relative_to(REPO_ROOT)} and {MANIFEST.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    if "--fixtures-only" in sys.argv:
        sys.exit(0)
    p = Pipeline()
    p.run()
    p.write_log()
