"""
Exercise 26 — the web search tool.

Course C, section: "The web search tool" (Tool Use block, final section).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    (paste the section URL here)
    Code from the official 006_web_search_complete.ipynb.
    NOTE: the org must enable web search first —
    https://console.anthropic.com/settings/privacy

WHAT THIS TEACHES
    The third species of tool, completing the set:
        exercise 19-23   user-defined     our schema, our execution
        exercise 25      Anthropic-defined their schema, OUR execution
        exercise 26      SERVER tool       their schema, THEIR execution
    Web search runs entirely on Anthropic's side, DURING the response:
    no tool_use stop, no run_tools, no loop. One request comes back with
    the search already done and the answer already cited.

    The schema stub:
        {"type": "web_search_20250305", "name": "web_search",
         "max_uses": 5}                       # cap on searches per request
    plus optionally "allowed_domains": [...] to fence the sources.

    The response content interleaves new block types:
        server_tool_use          the query Claude actually searched
        web_search_tool_result   the results (title + url per hit)
        text                     the answer — with block.citations
                                 attached: url, title, and the exact
                                 cited_text each claim rests on

    max_uses is 1.4 thinking applied to spend: the model may decide to
    follow up its own searches, and the cap is a programmatic fuse on
    that decision, not a suggestion.

EXAM LINK
    D1 — a server tool inverts the loop mental model: there is no
    stop_reason="tool_use" round-trip to manage (watch for
    stop_reason="pause_turn" instead — a long server-tool turn can pause
    and must be resent to continue). D2 — allowed_domains is a
    deterministic source fence: "only use reputable sources" in a prompt
    is guidance; a domain allowlist is enforcement. D4/D5 — citations
    carry the exact supporting text, making the answer AUDITABLE: the
    claim-source mapping 1.3 demanded of subagent handoffs, provided here
    by the platform.

RUN
    From the repo root (two searched requests, ~30-60s):
        .venv/bin/python academy/course-c-claude-api/exercises/26-the-web-search-tool.py

    MEASURED 2 Sep 2026, claude-sonnet-4-5:

    STAGE 1 — 22 blocks, 5 searches (= max_uses, the CAP FIRED: the model
    said it still lacked the 1.3.0 changelog and wanted more). Answer:
    anthropic SDK 1.3.0, released 1 Sep 2026, every claim carrying
    citations with cited_text. Two details worth keeping:
      - the model narrated its search strategy in interleaved text blocks
        and REFINED its query four times (version -> changelog -> quoted
        date -> GitHub release) — an agentic loop happening server-side,
        visible but not ours to run
      - it cited a third-party writeup confirming that SDK v1.0.0 removed
        temperature/top_p/top_k and Text Completions — independent
        confirmation of what exercise 06 measured empirically. The
        divergence table now has an external witness.

    STAGE 2 — NULL RESULT, and the day's best lesson: blocks=['text'],
    ZERO searches, zero citations. Including the schema makes search
    AVAILABLE, not used — for generic fitness advice the model judged its
    training data sufficient, so the nih.gov fence was never even tested
    (the 0/0 check below is vacuous). If the product requires searched,
    cited answers, availability is not enough: force it (tool_choice, or
    an instruction to search and cite) and VERIFY citations exist — an
    empty citations list is machine-checkable (D4).
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-sonnet-4-5"      # the notebook's choice for this section


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, message):
    messages.append({"role": "assistant", "content": message.content})


def chat(messages, tools=None, max_tokens=2000):
    params = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
    if tools:
        params["tools"] = tools
    return client.messages.create(**params)


def run_searched(messages, tools):
    """One request — but a long server-tool turn can come back with
    stop_reason='pause_turn', meaning 'not finished, send it back'. Loop
    on that (and only that): it is a continuation signal, not a request
    for us to execute anything."""
    while True:
        response = chat(messages, tools=tools)
        if response.stop_reason != "pause_turn":
            return response
        print("  (pause_turn — resending to continue the same turn)")
        add_assistant_message(messages, response)


def describe(response):
    print(f"stop_reason: {response.stop_reason}")
    print(f"blocks:      {[b.type for b in response.content]}")
    searches = getattr(response.usage, "server_tool_use", None)
    if searches:
        print(f"searches:    {searches.web_search_requests}")
    print()

    for block in response.content:
        if block.type == "server_tool_use":
            print(f">>> searched for: {block.input.get('query')!r}")
        elif block.type == "web_search_tool_result":
            hits = block.content if isinstance(block.content, list) else []
            print(f"    {len(hits)} results:")
            for hit in hits[:5]:
                print(f"      - {hit.title[:60]}  ({hit.url[:60]})")
        elif block.type == "text":
            print(f"text: {block.text[:300]}...")
            for citation in (block.citations or []):
                print(f"    [cite] {citation.url[:70]}")
                print(f"           \"{citation.cited_text[:90].strip()}...\"")
    print()


# ---------------------------------------- stage 1: unrestricted search
print("=" * 70)
print("STAGE 1 — unrestricted search (a question training data cannot answer)")
print("=" * 70)
messages = []
add_user_message(messages,
                 "What is the latest released version of the `anthropic` Python "
                 "SDK on PyPI, and what notable change did it introduce?")
response = run_searched(messages, tools=[{
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,
}])
describe(response)

# ------------------------------- stage 2: allowed_domains as a source fence
print("=" * 70)
print("STAGE 2 — allowed_domains=['nih.gov'] (the notebook's exact setup)")
print("=" * 70)
messages = []
add_user_message(messages, "What's the best exercise for gaining leg muscle?")
response = run_searched(messages, tools=[{
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,
    "allowed_domains": ["nih.gov"],
}])
describe(response)

# Did the fence hold? Check every citation's domain in code — trust, then
# verify, and verify deterministically.
cited = [c.url for b in response.content if b.type == "text"
         for c in (b.citations or [])]
outside = [u for u in cited if "nih.gov" not in u]
print(f"citations: {len(cited)}, outside nih.gov: {len(outside)}")
if outside:
    print("FENCE BREACHED:", outside)

# NOTES FROM THE COURSE
# - Server tool: include the schema, Claude searches, decides on follow-up
#   searches (capped by max_uses), reads results and answers — all within
#   one API request.
# - Response anatomy: server_tool_use (the query), web_search_tool_result
#   (the hits), text blocks carrying citations (url, title, cited_text).
# - allowed_domains restricts sources — the lesson's example fences
#   medical advice to nih.gov instead of hoping for authoritative blogs.
# - UI guidance from the lesson: sources list up top, citations inline —
#   the block structure is designed to be rendered, not just parsed.
#
# WORTH KNOWING (Domain 1 / 2 / 5)
# - Three tool species, one tools=[] parameter. What changes is who owns
#   the schema and who owns the execution — and therefore what YOUR loop
#   has to handle. Server tools need no loop at all (only pause_turn).
# - Citations are the platform doing 1.3's claim-source mapping for you.
#   When you build multi-agent synthesis, this is the shape to demand
#   from your own spokes.
# - Web searches bill per search on top of tokens — max_uses is a cost
#   gate as much as a behaviour gate.
