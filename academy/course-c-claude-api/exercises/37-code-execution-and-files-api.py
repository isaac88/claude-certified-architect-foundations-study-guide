"""
Exercise 37 — code execution and the Files API.

Course C, section: "Code execution and the Files API" (Features block close).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287777
    Code from the official 005_code_execution.ipynb; data is the lesson's
    streaming.csv (500 subscribers, 10 columns, Churned label) — GITIGNORED
    next to this file (course asset, public repo; re-download if missing).

WHAT THIS TEACHES
    Two features that only make sense together:
    - FILES API: upload once (client.files.upload), get a file_id, reference
      it forever — instead of re-encoding base64 into every request (the
      exercise-34 tax). Upload/list/delete are free; usage bills as input.
    - CODE EXECUTION: a server tool (like ex. 26's web search — their
      schema, their execution) that runs Python in an isolated container
      WITH NO NETWORK. The Files API is therefore the only door in or out:
      a container_upload block carries your file in; generated files come
      back as file_ids to download.
    The response is the course's richest block stream yet: text blocks
    interleaved with server_tool_use (the code Claude chose to run) and
    bash_code_execution_tool_result (stdout/stderr/return_code, plus
    bash_code_execution_output refs for files it created).

EXAM LINK
    D1 — a full agentic loop we neither wrote nor host: Claude iterates
    code -> result -> code inside one API turn (ex. 26's server-side loop,
    now with a REPL). D2 — the container boundary is a capability CONTRACT:
    no network is a guarantee, not a convention. D5 — delegated compute
    whose every step (code, stdout, exit code) is inspectable in blocks.

DIVERGENCES (this lesson has the most yet)
    - Tool type: page says code_execution_20250522, notebook already says
      code_execution_20250825 + TWO beta headers (code-execution-2025-08-25,
      files-api-2025-04-14) and client.beta.files.*. Current API: type
      code_execution_20260120, NO beta headers, stable client.files.*.
    - Result blocks renamed: code_execution_tool_result (lesson) is now
      bash_code_execution_tool_result / bash_code_execution_result, and
      generated-file refs are bash_code_execution_output (lesson:
      "code_execution_output").
    - The notebook's prompt warns "every execution starts with a completely
      clean slate — redeclare everything". code_execution_20260120 added
      REPL PERSISTENCE — variables survive across executions in the
      container — so the warning is obsolete on the current tool; prompt
      kept to the lesson page's version. Containers are also reusable
      across requests via response.container.id.
    - Notebook pins dated snapshot claude-sonnet-4-5-20250929; alias kept
      as everywhere in this repo. temperature dropped (SDK 1.2.0).

RUN
    From the repo root (ONE request, but Claude runs code inside it —
    expect 2-5 minutes; progress prints per block as it streams):
        .venv/bin/python academy/course-c-claude-api/exercises/37-code-execution-and-files-api.py

    MEASURED 6 Sep 2026, claude-sonnet-4-5 — ONE request, 360s, end_turn:
        24 code executions, 63 content blocks, input_tokens=513,365 (!),
        output=17,798. HALF A MILLION input tokens in one turn: the
        server-side loop re-reads the growing transcript per execution
        and every pass is billed — roughly $1.80 for this single request.
        Delegation is real, and so is its meter.
        Block stream: text / server_tool_use / bash_code_execution_
        tool_result AND text_editor_code_execution_tool_result — on
        20260120 the model drives the container with bash + text-editor
        commands (server_tool_use.input carries "command", not "code";
        it wrote analysis scripts as FILES, then ran them).
        Failure specimen, free of charge: /files/output/ ROTATES per
        execution. The model wrote its artefacts, then found the output
        dir empty, and regenerated everything — five times. 25 generated-
        file refs = 5 unique artefacts x 5 rounds; roughly half the 24
        executions and a large slice of the 513K tokens were spent
        chasing that moving directory. An environment invariant the
        agent did not know cost more than the analysis itself.
        The analysis itself: churn 38.6%; top driver customer-service
        interactions (0 interactions -> 0% churn, 6 -> 75%); low
        engagement 64.5% vs very-high 11.3%. Kept artefacts:
        37-churn_key_insights.png + 37-detailed_churn_report.txt
        (committed); the dashboard PNG has a visible defect — histogram
        mean lines plotted right of every bar — reviewed delegation,
        ex-25's lesson again.
        (The anatomy printer and download dedupe below were improved
        AFTER this run; a re-run prints the same story with better
        labels and 5 downloads instead of 25.)
"""

import time
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-sonnet-4-5"
HERE = Path(__file__).parent
CSV = HERE / "streaming.csv"


# ------------------------------------------------------- Files API helpers
def upload(file_path):
    """The notebook's upload helper on the stable namespace: explicit
    (filename, handle, mime) tuple so the CSV is typed as text/csv."""
    path = Path(file_path)
    with open(path, "rb") as f:
        return client.files.upload(file=(path.name, f, "text/csv"))


def download_file(file_id, dest_dir):
    metadata = client.files.retrieve_metadata(file_id)
    safe_name = Path(metadata.filename).name          # no path traversal
    dest = dest_dir / f"37-{safe_name}"
    client.files.download(file_id).write_to_file(dest)
    return dest


# ------------------------------------------------ stage 1: upload the CSV
print("=" * 70)
print("STAGE 1 — Files API: upload once, reference by id")
print("=" * 70)
file_metadata = upload(CSV)
print(f"uploaded {CSV.name} ({CSV.stat().st_size} bytes) -> "
      f"id={file_metadata.id}")

# ----------------- stage 2: the churn analysis, streamed block by block
print()
print("=" * 70)
print("STAGE 2 — container_upload + code_execution: the churn analysis")
print("=" * 70)
messages = [{
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "Run a detailed analysis to determine major drivers of "
                    "churn. Your final output should include at least one "
                    "detailed plot summarizing your findings.",
        },
        {"type": "container_upload", "file_id": file_metadata.id},
    ],
}]

t0 = time.perf_counter()
executions = 0
with client.messages.stream(
    model=MODEL,
    max_tokens=10000,
    messages=messages,
    tools=[{"type": "code_execution_20260120", "name": "code_execution"}],
) as stream:
    for event in stream:
        # Progress per block — a code-execution turn can run for minutes.
        if event.type == "content_block_start":
            btype = event.content_block.type
            if btype == "server_tool_use":
                executions += 1
                print(f"  [{time.perf_counter()-t0:5.1f}s] execution "
                      f"#{executions} starting...", flush=True)
            elif btype.endswith("tool_result"):
                print(f"  [{time.perf_counter()-t0:5.1f}s] result block "
                      f"({btype})", flush=True)
    response = stream.get_final_message()
elapsed = time.perf_counter() - t0

print(f"\nstop_reason={response.stop_reason}  {elapsed:.0f}s  "
      f"in={response.usage.input_tokens} out={response.usage.output_tokens}")
if getattr(response, "container", None):
    print(f"container id={response.container.id} (reusable via the "
          f"container= param; REPL state persists inside it)")

# ------------------------- walk the blocks: code, results, generated files
print()
print("=" * 70)
print("STAGE 3 — anatomy of the turn, and downloading what Claude made")
print("=" * 70)
generated = []
for block in response.content:
    if block.type == "text":
        print(f"\n[text] {' '.join(block.text.split())[:240]}...")
    elif block.type == "server_tool_use":
        # On code_execution_20260120 the input is NOT {"code": ...}: the
        # model drives the container with bash ({"command": ...}) and
        # text-editor commands — print whatever arrived.
        keys = list(block.input.keys()) if isinstance(block.input, dict) else []
        preview = " ".join(str(block.input).split())[:100]
        print(f"\n[server_tool_use] input keys={keys}: {preview}")
    elif block.type == "bash_code_execution_tool_result":
        result = block.content
        if result.type == "bash_code_execution_result":
            out = " ".join((result.stdout or "").split())[:160]
            print(f"[result] return_code={result.return_code} stdout: {out}")
            for ref in (result.content or []):
                if ref.type == "bash_code_execution_output":
                    generated.append(ref.file_id)
                    print(f"         generated file -> {ref.file_id}")
        else:
            print(f"[result] TOOL ERROR: {result.error_code}")
    else:
        print(f"\n[{block.type}]")

print(f"\nblock types: {[b.type for b in response.content]}")

print(f"\nDownloading generated file(s) via the Files API "
      f"({len(generated)} refs — the model may have regenerated the same "
      f"artefacts several times; skipping repeat filenames):")
seen = set()
for file_id in generated:
    name = Path(client.files.retrieve_metadata(file_id).filename).name
    if name in seen:
        continue
    seen.add(name)
    dest = download_file(file_id, HERE)
    print(f"  {file_id} -> {dest.name} ({dest.stat().st_size // 1024}KB)")

# NOTES FROM THE COURSE
# - Files API: upload -> metadata object -> reference the id in messages.
#   For repeated or large files, replaces base64-in-every-request.
# - Code execution: server tool, isolated Docker container, NO NETWORK,
#   multiple executions per conversation, results interpreted by Claude.
# - No network is why the two features pair: Files API in via
#   container_upload, generated artefacts out via download.
# - Only files CREATED by code execution can be downloaded — not your own
#   uploads (checked in the current docs; uploads are message inputs).
#
# WORTH KNOWING (current API, D1/D5)
# - This is the third tool species' full form (ex. 26 was the second
#   sighting): the agentic loop runs SERVER-SIDE inside one turn — code,
#   observe stdout, write more code — and the block stream is its
#   transcript. Our client wrote no loop at all.
# - Container reuse (response.container.id -> container= param) is 1.7's
#   session-state question at the sandbox level: state lives in the
#   container, requests can share it, and it expires — the same
#   resume-vs-fresh trade-off, relocated.
