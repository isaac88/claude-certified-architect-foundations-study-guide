"""Experiment runner for practice exercise 5 — Domain 2 tool contract lab.

Runs the four experiments from docs/exercises.md #5 against the live
support-desk MCP server + claude-opus-5, and writes MEASURED results to
experiment-log.md (the course-exercise habit: record what actually
happened, before/after, not what the theory predicts).

  1. Vague vs full descriptions -> routing of "check order #12345"
  2. Four error categories -> the loop reacts per category
     (retry / rephrase / explain / escalate)
  3. Valid-empty vs permission on get_customer -> "no such account" vs
     escalation, and neither gets retried
  4. tool_choice forcing get_customer first vs auto skipping it

Each experiment spawns a FRESH server process (fresh flaky-counter, chosen
TOOL_DESCRIPTIONS) — the same isolation .mcp.json gives each Claude Code
session.

Run:  ../../.venv/bin/python experiments.py        (from this directory)
"""

import asyncio
import json
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from client_loop import MCPClient, SupportAgent, MODEL

LAB_DIR = Path(__file__).parent
REPO_ROOT = LAB_DIR.parent.parent
SERVER = LAB_DIR / "mcp_server.py"
LOG = LAB_DIR / "experiment-log.md"

# The course project keeps ANTHROPIC_API_KEY in academy/course-c-claude-api/.env;
# reuse it (load_dotenv never overrides an already-exported variable).
load_dotenv(REPO_ROOT / "academy" / "course-c-claude-api" / ".env")


def server_env(descriptions: str) -> dict:
    """Env for one server process. SUPPORT_DESK_API_KEY simulates the secret
    that .mcp.json injects via ${ENV_VAR} — any value satisfies the lab
    server, but it MUST be present (the server exits if the expansion broke).
    """
    return {
        **os.environ,
        "SUPPORT_DESK_API_KEY": os.environ.get("SUPPORT_DESK_API_KEY", "lab-dummy-key"),
        "TOOL_DESCRIPTIONS": descriptions,
    }


async def run_once(
    descriptions: str, prompt: str, tool_choice: dict | None = None, model: str = MODEL
) -> dict:
    """One conversation against one fresh server process."""
    async with MCPClient(
        command=sys.executable, args=[str(SERVER)], env=server_env(descriptions)
    ) as mcp_client:
        agent = SupportAgent(mcp_client, model=model)
        return await agent.run(prompt, tool_choice=tool_choice)


def fmt_calls(trace: dict) -> str:
    """Render the tool-call trace as markdown list lines."""
    if not trace["tool_calls"]:
        return "  - (no tool calls)\n"
    out = ""
    for c in trace["tool_calls"]:
        retries = f", harness retries: {c['retries']}" if c["retries"] else ""
        out += (
            f"  - turn {c['turn']}: `{c['tool']}({json.dumps(c['input'])})` "
            f"→ **{c['category']}**{retries}\n"
        )
    return out


def fmt_run(title: str, prompt: str, trace: dict) -> str:
    return (
        f"**{title}** — prompt: “{prompt}”\n\n"
        + fmt_calls(trace)
        + f"  - final: “{trace['final_text'].strip()[:600]}”\n\n"
    )


# ---------------------------------------------------------------------------
# Experiment 1 — vague vs full descriptions (2.1 misrouting)
# ---------------------------------------------------------------------------
async def experiment_1() -> str:
    prompt = "check order #12345"
    md = "## Experiment 1 — vague vs full descriptions, same input\n\n"
    md += (
        "Vague set: `get_customer` = “Check customer accounts and orders.”, "
        "`lookup_order` = “Get a record.” — overlapping one-liners; the word "
        "“orders” sits in the WRONG tool's description.\n\n"
        "Tool NAMES still carry routing signal, so the vague set is sampled "
        "3× per model (routing under ambiguity is stochastic), on the "
        f"skill-default `{MODEL}` and on `claude-haiku-4-5` (the course's "
        "model — smaller models lean harder on descriptions).\n\n"
        "| model | descriptions | trial | first tool call | routed |\n"
        "|---|---|---|---|---|\n"
    )
    example_traces = []
    for model in (MODEL, "claude-haiku-4-5"):
        for variant, trials in (("vague", 3), ("full", 1)):
            for trial in range(1, trials + 1):
                trace = await run_once(variant, prompt, model=model)
                first = (
                    trace["tool_calls"][0]["tool"] if trace["tool_calls"] else "(none)"
                )
                verdict = "✅" if first == "lookup_order" else "❌ misroute"
                md += f"| `{model}` | {variant} | {trial} | `{first}` | {verdict} |\n"
                # keep one full trace per (model, variant) for the log body
                if trial == 1:
                    example_traces.append((f"{model} / {variant}", trace))
    md += "\n"
    for title, trace in example_traces:
        md += fmt_run(title, prompt, trace)

    # Probe B — measured follow-up. Probe A came back 8/8 correct even on
    # the vague set: the tool NAME (`lookup_order`) plus the word "order" in
    # the prompt was enough signal on its own. Names are part of the 2.1
    # contract too. So probe B removes the word "order" from the input:
    # a bare "check on #12345" is only routable via the DESCRIPTIONS —
    # the full lookup_order description documents the ORD-XXXXX id format
    # and the normalise-bare-numbers rule; the vague set documents nothing.
    prompt_b = "Can you check on #12345 for me?"
    md += (
        "### Probe B — input without the word “order”: description is the "
        "only signal\n\n"
        f"Prompt: “{prompt_b}”. The full `lookup_order` description names the "
        "id format (ORD- + 5 digits) and tells the model to normalise bare "
        "numbers; the vague set (“Get a record.” / “Check customer accounts "
        "and orders.”) gives no way to tell what #12345 is.\n\n"
        "| model | descriptions | trial | first tool call | routed |\n"
        "|---|---|---|---|---|\n"
    )
    example_traces = []
    for model in (MODEL, "claude-haiku-4-5"):
        for variant, trials in (("vague", 3), ("full", 1)):
            for trial in range(1, trials + 1):
                trace = await run_once(variant, prompt_b, model=model)
                first = (
                    trace["tool_calls"][0]["tool"] if trace["tool_calls"] else "(none)"
                )
                verdict = "✅" if first == "lookup_order" else f"❌ ({first})"
                md += f"| `{model}` | {variant} | {trial} | `{first}` | {verdict} |\n"
                if trial == 1:
                    example_traces.append((f"{model} / {variant}", trace))
    md += "\n"
    for title, trace in example_traces:
        md += fmt_run(title, prompt_b, trace)
    return md


# ---------------------------------------------------------------------------
# Experiment 2 — the four error categories drive four different reactions
# ---------------------------------------------------------------------------
async def experiment_2() -> str:
    md = "## Experiment 2 — four error shapes, four reactions\n\n"

    # transient: ORD-00503 fails twice then succeeds; the HARNESS retries.
    trace = await run_once("full", "What's the status of order ORD-00503?")
    md += fmt_run("TRANSIENT → harness retry with backoff", "status of ORD-00503", trace)

    # validation: pin the malformed argument so the tool (not the model's
    # own normalisation) surfaces the error; the model must then FIX it.
    trace = await run_once(
        "full",
        "Call lookup_order with order_id set to exactly the string '12345' "
        "first — do not reformat it on the first call. Then get me the order status.",
    )
    md += fmt_run("VALIDATION → model fixes the argument and retries", "lookup_order('12345') forced malformed", trace)

    # business: over the £100 self-serve limit; expect explain, no retry.
    # First measured run showed the model PRE-EMPTING the doomed call — the
    # tool description states the limit, so it explained without calling
    # process_refund at all (the contract worked one layer earlier than
    # planned). To capture the BUSINESS error on the wire, the prompt pins
    # the policy decision on the refund system, not the model.
    trace = await run_once(
        "full",
        "Please refund the full £549.00 for order ORD-22222; the customer is "
        "CUST-2002. Submit it through process_refund regardless of what you "
        "expect — policy decisions are made by the refund system, not by you.",
    )
    md += fmt_run("BUSINESS → explain with customer-safe text, no retry", "£549 refund on ORD-22222 (submit regardless)", trace)

    # permission: restricted account; expect ESCALATE, no retry.
    trace = await run_once("full", "Pull up the account for Margaret Hamilton.")
    md += fmt_run("PERMISSION → escalate, no retry", "account for Margaret Hamilton", trace)
    return md


# ---------------------------------------------------------------------------
# Experiment 3 — valid empty result vs permission error (the exam favourite)
# ---------------------------------------------------------------------------
async def experiment_3() -> str:
    md = "## Experiment 3 — `[]` (no such account) vs permission error\n\n"

    trace = await run_once("full", "Find the account for Ada Lovelace.")
    lookups = [c for c in trace["tool_calls"] if c["tool"] == "get_customer"]
    md += fmt_run(
        f"VALID EMPTY — get_customer called {len(lookups)}× "
        f"({'no retry ✅' if len(lookups) == 1 else 'RETRIED ❌'})",
        "Find the account for Ada Lovelace.",
        trace,
    )

    trace = await run_once("full", "Find the account for Margaret Hamilton.")
    lookups = [c for c in trace["tool_calls"] if c["tool"] == "get_customer"]
    escalated = trace["final_text"].strip().upper().startswith("ESCALATE")
    md += fmt_run(
        f"PERMISSION — get_customer called {len(lookups)}×, "
        f"escalated: {'✅' if escalated else '❌'}",
        "Find the account for Margaret Hamilton.",
        trace,
    )
    return md


# ---------------------------------------------------------------------------
# Experiment 4 — tool_choice forces get_customer first
# ---------------------------------------------------------------------------
async def experiment_4() -> str:
    # A prompt that hands the model everything it needs for a refund, so
    # under "auto" verifying the customer first looks skippable.
    prompt = (
        "Process a £20 refund on order ORD-12345. The customer is Grace "
        "Hopper, customer id CUST-1001."
    )
    md = "## Experiment 4 — `tool_choice` forces `get_customer` first\n\n"

    trace = await run_once("full", prompt)  # tool_choice defaults to auto
    first = trace["tool_calls"][0]["tool"] if trace["tool_calls"] else "(none)"
    md += fmt_run(f"AUTO — first call: `{first}`", prompt, trace)

    forced = {"type": "tool", "name": "get_customer"}
    trace = await run_once("full", prompt, tool_choice=forced)
    first = trace["tool_calls"][0]["tool"] if trace["tool_calls"] else "(none)"
    md += fmt_run(
        f"FORCED `{{type: tool, name: get_customer}}` — first call: `{first}` "
        f"({'✅ cannot skip' if first == 'get_customer' else '❌'})",
        prompt,
        trace,
    )
    md += (
        "> Note: forcing a tool is incompatible with extended thinking, and "
        f"on `{MODEL}` thinking is on by default — the forced request also "
        "sends `thinking: {type: disabled}` (see client_loop.py). On "
        "Fable 5.1 forced `tool`/`any` is removed entirely (400): the "
        "substitute is `auto` + an explicit prompt instruction.\n\n"
    )
    return md


async def main():
    sections = [
        f"# Experiment log — exercise 5, tool contract lab ({date.today().isoformat()})\n\n"
        f"Model: `{MODEL}` · server: mcp_server.py (stdio) · every run spawns a fresh server.\n\n",
        await experiment_1(),
        await experiment_2(),
        await experiment_3(),
        await experiment_4(),
    ]
    LOG.write_text("".join(sections))
    print(f"Wrote {LOG}")


if __name__ == "__main__":
    asyncio.run(main())
