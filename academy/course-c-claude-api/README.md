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
| 06 | [06-temperature.py](exercises/06-temperature.py) | Generation as tokenize → predict → sample; what temperature does to the sampling step; the lesson's task ranges | **D1 + D4** — temperature 0 is **not** determinism: 3 runs at `temperature=0.0` gave 3 distinct answers. Deterministic requirements need code, not a sampling knob | [287728](https://anthropic.skilljar.com/claude-with-the-anthropic-api/287728) |
| 07 | [07-response-streaming.py](exercises/07-response-streaming.py) | 5-stage journey: measure time-to-first-output → raw `stream=True` events → `text_stream` → `get_final_message()` → what the helper hides | **D5** — perceived latency and reliability. Measured 6.87s → 3.29s to first output. Streaming is **mandatory** at large `max_tokens` to avoid HTTP timeouts | _(paste section URL)_ |
| 08 | [08-structured-data.py](exercises/08-structured-data.py) | 4 stages: the wrapping problem → prefill + `stop_sequences` working on a dated snapshot → the same code 400ing on a current model → `output_config.format` schema | **D4** — request vs guarantee. Prefill is **removed** (400); `stop_sequences` still works. Structured outputs return bare JSON with the shape enforced | [287732](https://anthropic.skilljar.com/claude-with-the-anthropic-api/287732) |
| 09 | [09-structured-data-exercise.py](exercises/09-structured-data-exercise.py) | The slide task, two prefills compared: a fenced block (bare runnable commands) vs a numbered list (`1. aws` + stop `["4."]`) | **D4 + D4.4** — **the stop marker decides what is bounded**: `["4."]` caps the count, `["```"]` caps only the block (asked for ten, got ten, still `stop_reason=stop_sequence`). Schemas enforce shape but not cardinality, so exactly-three needs code validation | [287732](https://anthropic.skilljar.com/claude-with-the-anthropic-api/287732) |
| 10 | [10-generating-test-datasets.py](exercises/10-generating-test-datasets.py) | Step 1 of an eval pipeline: Haiku generates the input dataset via prefill + `stop_sequences`, saved to `dataset.json` | **D4** — the dataset is the experimental **control**. Note **prefill still works on Haiku 4.5** but 400s on Opus 5, so the lesson's technique is valid here and not portable upward | _(paste section URL)_ |
| 11 | [11-running-the-eval.py](exercises/11-running-the-eval.py) | The pipeline: `run_prompt` → `run_test_case` → `run_eval`, over `dataset.json`, with grading still a hardcoded 10 | **D4** — the bare prompt returns ~600 words for "write a regex"; the eval is what makes that visible. Sequential loop: 60s for 3 cases | _(paste section URL)_ |
| 12 | [12-model-based-grading.py](exercises/12-model-based-grading.py) | `grade_by_model` — a second model returns strengths/weaknesses/reasoning **and** a 1-10 score; `run_eval` averages them | **D4 + D5.3** — three failure modes, all real: a model grader **confabulates a review of an empty output**; prefill-based grading breaks on regex solutions (`Invalid escape`) so the grader uses a **schema**; and an ungraded case must **not** score 0 — that alone moved the average 7.33 → 3.67 | _(paste section URL)_ |
| 13 | [13-code-based-grading.py](exercises/13-code-based-grading.py) | `grade_syntax` — `json.loads`/`ast.parse`/`re.compile` score 10 or 0, dispatched on the dataset's `format` field; v2 prompt (code only, no commentary) + `"```code"` prefill; final score = average of code and model graders | **D4** — syntax is mechanically checkable, so a **parser** grades it, not a judge. Baseline moved 7.3-7.5 → 8.3-8.6 and solves got ~5× faster. Also: with prefill, `stop_reason=stop_sequence` is the **success** value — and run 2 proved it can hold that value with **0 chars** captured (model closed the prefilled fence immediately), so the guard must check emptiness too | _(paste section URL)_ |
| 14 | [14-exercise-on-prompt-evals.py](exercises/14-exercise-on-prompt-evals.py) | The section's exercise: dataset generation also emits a `solution_criteria` per case, and `grade_by_model` receives it in a `<criteria>` block — the rubric is authored once, at dataset time, not improvised by the grader per call | **D4** — control the **judge**, not just the inputs: without pinned criteria, score drift mixes "the prompt changed" with "the grader changed its mind". Verified live: criteria demanded case-insensitive matching, the solution missed it, the grader cited that criterion and scored it lowest. Regenerating the dataset **retires the exercise-13 baseline** — new control, comparisons restart here | _(paste section URL)_ |
| 15 | [15-prompt-engineering.py](exercises/15-prompt-engineering.py) | Start of the **prompt engineering block**: the iterate cycle (goal → prompt → evaluate → one technique → re-evaluate) run once with a deliberately naive meal-plan prompt to set the baseline. Uses [prompt_evaluator.py](exercises/prompt_evaluator.py) — the course's `PromptEvaluator` scaffolding (threaded generation/grading, structured `prompt_inputs`, mandatory `extra_criteria`, HTML report), adapted per its header | **D4** — the control arm: no technique counts until it moves a measured number. Baseline **4.67** (2, 5, 7) — the lesson expects ~2.3; today's Haiku is stronger. The spread (2 vs 7 on the same prompt) is the real defect: unreliability, not a low mean. Block has its own control (`dataset-meal-plan.json`), generated once. Also: notebook bug found — `{prompt_inputs_spec}` placeholder never substituted (render key mismatch), failing silently | _(paste section URL)_ |
| 16 | [16-being-specific.py](exercises/16-being-specific.py) | Technique 1: output quality guidelines (use nearly always) vs process steps (for multi-angle problems). v2 = exercise 15's naive prompt + the lesson's six guidelines — the **only** change in the iteration | **D4** — measured **4.67 → 8.33**, and the spread collapsed 2–7 → 7–9: the baseline's worst case (+7) gained most, so specificity buys **reliability first, quality second**. The guidelines mirror the eval's mandatory criteria — prompt and rubric are two copies of one contract; when one changes, change the other | _(paste section URL)_ |
| 17 | [17-structure-with-xml-tags.py](exercises/17-structure-with-xml-tags.py) | Technique 2: fence interpolated data in descriptive tags (`<athlete_information>`, `<my_code>`/`<docs>`) so instruction/data boundaries are explicit. v3 = v2 + tags, structure only | **D4** — the discipline lesson: scored **9, 9, 9** (v2: 8.33/7.67, noise ~0.7), so the mean gain is *at* the noise floor and unclaimable from one run — as the lesson predicts for simple prompts. First zero-spread run of the block, though. Real payoffs (mixed content at scale, injection resistance) are invisible to this metric — the eval itself has used `<task>`/`<solution>`/`<criteria>` tags since ex. 12 | _(paste section URL)_ |
| 18 | [18-providing-examples.py](exercises/18-providing-examples.py) | Technique 3: one-shot/multi-shot — freeze a top-scoring eval output into the prompt as `<sample_input>`/`<ideal_output>`, say *why* it is ideal. v4 = v3 + the 9/10 rock-climber plan from ex. 17, frozen in the file (never loaded at runtime — a measured prompt version must not drift) | **D4** — scored **8.33** vs v3's 9.00: within noise, null result, as ceiling predicts. Three production lessons: **contamination** (the example IS a test case — train/test separation applies to prompts; even so, that case scored *lower*, 8), **cost** (~3× input tokens per request for no measured gain — examples are a per-request tax), and **flawed ideals ship** (the example's totals contradict its own target) | _(paste section URL)_ |
| 19 | [19-tool-functions-and-schemas.py](exercises/19-tool-functions-and-schemas.py) | Start of the **Tool Use block**: a tool = ordinary Python function (ours, never sent) + JSON schema (sent with every request). Claude replies with a `tool_use` block — id, name, input — it *asks*, never executes. Stops deliberately before answering the request (that's ex. 20) | **D1.1 + D2** — measured reply: `stop_reason=tool_use`, `blocks: ['tool_use']` — **no text block at all**, so `content[0].text` raises on this exact response. Prose "March 15, 2026" became ISO `2026-03-15` purely from the schema's description — argument filling is schema-driven translation, and the input is unvalidated model output (D2: the `unit` field begs for an enum) | _(paste section URL)_ |

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
| `add_assistant_message(messages, "```json")` + `stop_sequences=["```"]` | `output_config={"format": {"type": "json_schema", "schema": {...}}}` on current models; **prefill still works on `claude-haiku-4-5`** (verified 1 Sep 2026, exercise 10) | **Assistant prefill is removed on the current top tier**: `400 "This model does not support assistant message prefill. The conversation must end with a user message."` Isolated by testing — prefill alone 400s, `stop_sequences` alone still works, dated snapshots still accept prefill. Structured outputs replace the hack with an enforced schema. Note strict schemas need `additionalProperties: False` on **every** object, nested included |
| `chat(messages, system=None, temperature=1.0)` | **No sampling parameters at all** | `temperature`, `top_p` and `top_k` are **removed from anthropic SDK 1.2.0** — `TypeError` before any request. Raw HTTP to `claude-opus-5` returns `400 "temperature is deprecated for this model."` Dated snapshots (e.g. `claude-sonnet-4-5-20250929`) still accept it. Nearest current lever is `output_config.effort`, which trades thoroughness against cost — not a creativity dial |
| `.env` as `ANTHROPIC_API_KEY="key"` (quoted) | Unquoted | `python-dotenv` strips the quotes, but a shell `source` of the same file keeps them and auth fails. This repo writes it unquoted so both the Python and curl paths work |

Model IDs are the most common divergence — these notes use `claude-opus-5`. If the video uses an older ID, that is fine for the video; do not copy it forward.
