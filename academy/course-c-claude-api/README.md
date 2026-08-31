# Course C — Building with the Claude API

Code written along with the Anthropic Academy instructor, kept here so it can be re-read during revision. Course card: Anthropic Academy → *Prepare for this exam* → **Building with the Claude API** (level 100–200).

**Course:** <https://anthropic.skilljar.com/claude-with-the-anthropic-api> (Skilljar login required)

Pairs with **Domain 1** ([domains/01-agentic-architecture](../../domains/01-agentic-architecture/)) and feeds Domains 2, 4 and 5.

## Getting an API key

The exercises need API credit. Console billing is **separate** from a Claude.ai Pro/Max subscription — a subscription grants no API credit.

1. **console.anthropic.com** → sign in → **Settings → API keys → Create key**.
2. Copy it at once (shown only once). It starts `sk-ant-`.
3. Put it in `.env` in this folder as `ANTHROPIC_API_KEY=sk-ant-...`. Never in an exercise file.
4. Add prepaid credit under **Billing** if the org has none.

Alternative with no key on disk — the `ant` CLI. **Already installed** via [`mise.toml`](../../mise.toml) at the repo root (v1.28.0), so `cd` to the repo and `ant` is on your PATH:

```bash
ant auth login
ant messages create --model claude-opus-5 --max-tokens 1024 \
  --message '{role: user, content: "Hello, Claude"}'
```

Per the docs, `ant auth login` "opens a browser-based OAuth flow **against the Claude Console** and stores the resulting credentials locally, so you can call the API without creating or managing an API key." So it removes the need to *manage a key* — it does **not** remove the need for a Console org with billing, and it cannot mint an `sk-ant-` key. The SDK reads the stored profile automatically, so `Anthropic()` works with no `.env`.

Then either `ant messages create` as above, or the curl script with `USE_OAUTH=1 bash reference/raw-http.sh` — it fetches a short-lived token via `ant auth print-credentials --access-token` and sends it as `Authorization: Bearer`. The token is captured by command substitution and never echoed: **do not print a credential to a terminal, a log, or an agent transcript.**

`ant messages create` is worth using for study in its own right: typed flags instead of hand-written JSON, and it prints the full API object — `content` block list, `stop_reason`, `usage` — which is the exact shape Domain 1 tests. Docs: <https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart>

**Use a personal Console org, not an employer's**, unless you have cleared it — this is a personal study repo, and a work key bills the company and dies when you leave.

### If an employer-managed email cannot create a Console org

Anthropic lets an organisation claim its email domain. Where that is in force, signing up for the Console with an address on that domain is refused — the parent organisation blocks new org creation, and there is no terminal-side workaround. **Use a personal email:**

1. Private/incognito browser window (otherwise it reuses the existing session).
2. Sign up at platform.claude.com with a personal email; create the org.
3. Add ~$5 credit — plenty for this course.
4. `ant auth login --profile study`, signed in as the personal account.
5. `ANTHROPIC_PROFILE=study ant messages create --model claude-opus-5 --max-tokens 1024 --message '{role: user, content: "Hello, Claude"}'`

The named profile (`study`) keeps this isolated from any other credential. The curl script takes it too: `USE_OAUTH=1 ANT_PROFILE=study bash reference/raw-http.sh`.

Requesting an exception, or a seat in an employer's Console org, is the wrong route for personal certification study — someone else's billing, someone else's audit logs, and access that vanishes when you change role.

### A Claude subscription is not API access (checked 31 Aug 2026)

Pro, Max, **Team** and Enterprise plans do **not** include the API or Console, and cannot mint `sk-ant-` keys — Anthropic's wording: *"A paid Claude subscription enhances your chat experience but doesn't include access to the Claude API or Console."* Plan usage credits cover Claude apps and Claude Code terminal usage, not the API.

Two different things get called OAuth:

- **Subscription OAuth** — what Claude Code uses on a Pro/Max/Team seat. Scoped to Claude Code; not a general API credential.
- **Console OAuth** (`ant auth login`) — a real API credential, but it still resolves to a Console org with pay-as-you-go API billing. It changes *how* you authenticate, not *who pays*.

Either way a Console organisation with its own billing is required. Source: <https://support.claude.com/en/articles/9876003>

Cost: exercises here are a few hundred tokens each; a hundred runs is pennies. The real risk is a buggy agent loop that never stops — which is the Domain 1 lesson.

## Setup (done once — already done)

```bash
cd academy/course-c-claude-api
cp .env.example .env          # then paste your real key into .env
chmod 600 .env
```

There is **one** virtualenv for the whole repo, at the repo root — that is the one VS Code and other IDEs select automatically. It is already installed. To rebuild from scratch, from the repo root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r academy/course-c-claude-api/requirements.txt
```

Do not create a second venv inside this folder; two environments with drifting versions is how "works in one terminal, not the other" starts.

`.env` and `.venv/` are gitignored. **Never paste a real API key into an exercise file** — it belongs in `.env` only.

## Run an exercise

From the **repo root**:

```bash
.venv/bin/python academy/course-c-claude-api/exercises/01-first-request.py
```

`load_dotenv()` finds the key by walking up from the script's own directory until it hits a `.env` — so `academy/course-c-claude-api/.env` is picked up wherever you invoke Python from. That is also why `load_dotenv()` fails when a script is piped in on stdin: there is no file to walk up from. Pass an explicit path in that case.

## Exercise index

| # | File | Teaches | Exam link | Source |
|---|---|---|---|---|
| 01 | [01-first-request.py](exercises/01-first-request.py) | One `POST /v1/messages`; `content` is a list of blocks; `stop_reason`; `usage` | D1 — the block list is why the 1.1 bug happens | _(scaffold, not a course section)_ |
| 02 | [02-making-a-request.py](exercises/02-making-a-request.py) | `create()`'s three params; `max_tokens` as a ceiling not a target; user/assistant roles; extracting text | **D1/1.1** — runs the course's `content[0].text` beside the safe version; the course's version raises `AttributeError` | [287725](https://anthropic.skilljar.com/claude-with-the-anthropic-api/287725) |
| 03 | [03-multi-turn-conversations.py](exercises/03-multi-turn-conversations.py) | The API is **stateless**; you own the `messages` list; append Claude's reply as an `assistant` message and resend everything | **D1.1 + D1.7** — 3 stages: no history → with history → what a string history discards (annotation) | _(paste section URL)_ |
| 04 | [04-chat-bot-exercise.py](exercises/04-chat-bot-exercise.py) | Interactive loop over the three helpers: `input` → append → call → append → print → repeat. Prints per-turn and session token usage | **D1.1** — the simplest agentic loop; swap the human for `stop_reason` and it becomes the 1.1 loop. Also shows input tokens growing as history is resent | _(paste section URL)_ |
| 05 | [05-system-prompts.py](exercises/05-system-prompts.py) | `system` as a **top-level** parameter (not a message); the maths-tutor contrast; `chat(messages, system=None)` with conditional kwargs | **D4** — explicit, testable criteria beat vague instruction. Also shows the system prompt's per-request token cost and why `system=None` is a 400 | _(paste section URL)_ |

Add a row per exercise as the course goes on.

## Reference (not course exercises)

Written by the instructor-agent, not the video. Kept separate so course numbering stays clean.

| File | Teaches |
|---|---|
| [reference/history-replay-with-tools.py](reference/history-replay-with-tools.py) | Why the assistant history must keep **blocks**, not text. A tool turn can return no text block at all; a string history loses `tool_use` and the next call fails with a live 400; preserving `response.content` fixes it. **D1.1** |
| [reference/response-shapes.md](reference/response-shapes.md) | **Study this if you have no API credit.** The response shapes the exam tests — text-only, `tool_use` (task 1.1 on the wire), error — with provenance labelled, plus the `stop_reason` table and hand-writing drills |
| [reference/raw-http.sh](reference/raw-http.sh) | The same request as raw curl — the wire shape the exam actually tests. Supports an API key (`x-api-key`) or Console OAuth (`Authorization: Bearer` + `anthropic-beta: oauth-2025-04-20`). Also demonstrates **error propagation (D5.3)**: curl exits 0 on a 401, so the status is captured with `-w` and mapped to a non-zero exit |

**No key yet?** The exam is closed-book multiple choice — you never execute a request during it. Read `reference/raw-http.sh` for the shape, write requests by hand, and have them marked in chat. A missing key delays running the exercises; it does not block exam preparation or the domain steps.

## House rules for these files

**Naming:** `NN-<course-section-title-in-kebab-case>.py`, so a file names the lesson it came from and the two line up when revising. Files not drawn from a course section keep a descriptive name instead.

Each exercise file carries a docstring header with four parts, so a file read six weeks later still explains itself:

1. **WHAT THIS TEACHES** — the mechanism, in one or two sentences.
2. **SOURCE** — the Skilljar URL of the course section it came from, so the lesson can be re-watched.
3. **EXAM LINK** — which domain and task statement it maps to, if any.
4. **RUN** — the exact command.
5. **NOTES FROM THE COURSE** — comment lines at the bottom, filled in while watching.

Working code only. If an exercise is deliberately broken to show a failure mode, say so in the header and name the fix.

**Scope discipline:** an exercise covers what its course section covers, no more. Material from later topics — or from outside the course — goes in `reference/`, and the exercise links to it. A short annotation on something the section itself introduces (a helper it defines, say) may stay inline if it is labelled as an annotation.

## Where the course and current API differ

The Academy videos were recorded against an earlier API surface. When the instructor's code differs from what works today, keep **both**: write the current shape in the file and record the instructor's version in `NOTES FROM THE COURSE`. Divergences seen so far:

| Instructor shows | Current API | Why |
|---|---|---|
| `model = "claude-sonnet-4-0"` | `claude-opus-5` (or `claude-sonnet-5`) | Checked 31 Aug 2026 with `client.models.list()`: `claude-sonnet-4-0` is **not in the list**. Live IDs: `claude-opus-5`, `claude-sonnet-5`, `claude-fable-5`, `claude-opus-4-8/4-7/4-6`, `claude-sonnet-4-6`, plus dated 4.5 snapshots |
| `message.content[0].text` | Iterate `content`, filter `block.type == "text"` | **The exam's anti-pattern, taught as the happy path.** Current models return a `thinking` block first, so this raises `AttributeError: 'ThinkingBlock' object has no attribute 'text'`. Verified in exercise 02 |
| `chat()` returning `message.content[0].text` | Return the message; extract with a type filter | Raises `AttributeError` whenever the first block is `thinking` or `tool_use`. On a tool turn there may be **no** text block at all — verified: `blocks: ['tool_use']` |
| `add_assistant_message(messages, answer)` storing a **string** | Append `response.content` (the block list) | A string discards `thinking` blocks and **destroys `tool_use` blocks**. The next turn is then rejected: `400 … Each 'tool_result' block must have a corresponding 'tool_use' block in the previous message.` Verified in [reference/history-replay-with-tools.py](reference/history-replay-with-tools.py) — tools are not part of the multi-turn lesson itself |
| `.env` as `ANTHROPIC_API_KEY="key"` (quoted) | Unquoted | `python-dotenv` strips the quotes, but a shell `source` of the same file keeps them and auth fails. This repo writes it unquoted so both the Python and curl paths work |

Model IDs are the most common divergence — these notes use `claude-opus-5`. If the video uses an older ID, that is fine for the video; do not copy it forward.
