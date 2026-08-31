# Messages API response shapes

Study material for when you cannot execute requests. The exam is closed-book multiple choice — you are scored on **recognising** these shapes, never on running them.

Provenance is labelled on each block. Nothing here is invented output presented as a real capture.

---

## 1. Text-only response — `stop_reason: "end_turn"`

*Source: official [CLI quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart) documentation example.*

```json
{
  "model": "claude-opus-5",
  "id": "msg_01YMmR5XodC5nTqMxLZMKaq6",
  "type": "message",
  "role": "assistant",
  "content": [
    { "type": "text", "text": "Hello! How are you doing today?" }
  ],
  "stop_reason": "end_turn",
  "usage": { "input_tokens": 27, "output_tokens": 20 }
}
```

Three things to burn in:

- `content` is an **array**, always — even for one text block.
- `stop_reason: "end_turn"` is the *only* legitimate signal that the turn is finished.
- `usage` is per-request, not cumulative. You add it up yourself across a loop.

### Real capture — and a thinking block in position 0

*Source: genuinely captured in this repo on 31 Aug 2026 by running `exercises/01-first-request.py` against `claude-opus-5`.*

```
stop_reason: end_turn
block types: ['thinking', 'text']
usage: 21 in / 161 out
```

`content[0]` was **`thinking`**, not `text`. Current models run adaptive thinking by default, so reasoning arrives as its own block ahead of the answer.

This sharpens the 1.1 lesson. The buggy `if response.content[0].type == "text"` is not merely *often* wrong — the type at position 0 varies with the model, the thinking configuration and the turn, and may be `thinking`, `text` or `tool_use`. **No index in `content` is safe to assume.** Iterate the list and branch on `stop_reason`.

Thinking blocks also have a replay rule: pass them back unchanged when continuing on the same model.

#### The same response in raw JSON — two things the SDK printout hides

*Source: genuinely captured on 31 Aug 2026 via `reference/raw-http.sh`, HTTP 200.*

```json
{
  "content": [
    { "type": "thinking", "thinking": "", "signature": "CAIS/AIKjgEIERgCKkD7P5..." },
    { "type": "text", "text": "An agentic loop is the iterative cycle in which..." }
  ],
  "stop_reason": "end_turn",
  "stop_details": null,
  "usage": {
    "input_tokens": 21,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "output_tokens": 166,
    "output_tokens_details": { "thinking_tokens": 48 },
    "service_tier": "standard",
    "inference_geo": "global"
  }
}
```

1. **`"thinking": ""` — empty.** Thinking `display` defaults to `"omitted"` on current models, so the block and its `signature` arrive with no reasoning text. Set `thinking: {type: "adaptive", display: "summarized"}` if you want a readable summary.
2. **48 thinking tokens were billed anyway.** Thinking happens and costs money whether or not you can see it. Visibility and billing are independent — a cost-model point that only the raw `usage` reveals.

Also note `stop_details: null`. It is populated **only** when `stop_reason` is `"refusal"`, so guard before reading it. And `cache_read_input_tokens: 0` is the field to watch when diagnosing prompt caching — if it stays 0 across repeated identical prefixes, something is silently invalidating the cache.

---

## 2. Tool-use response — `stop_reason: "tool_use"`

*Source: documented shape from the Messages API tool-use specification. Structure is authoritative; the ids and text are illustrative.*

```json
{
  "id": "msg_...",
  "type": "message",
  "role": "assistant",
  "content": [
    { "type": "text", "text": "Let me look that up for you." },
    {
      "type": "tool_use",
      "id": "toolu_01A09q90qw90lq917835lq9",
      "name": "lookup_order",
      "input": { "order_id": "ORD-8841" }
    }
  ],
  "stop_reason": "tool_use",
  "usage": { "input_tokens": 412, "output_tokens": 76 }
}
```

**This is the whole of task 1.1, on the wire.** Read it again and note:

- `content[0].type` is `"text"`. `content[1].type` is `"tool_use"`.
- Code branching on `content[0].type == "text"` returns the chatty preamble and **never executes the tool**. The customer sees "Let me look that up for you." and nothing happens.
- `stop_reason` is `"tool_use"` — unambiguous, and the reason the field exists.
- A message may hold **several** `tool_use` blocks. Execute all of them.

### What you send back

A **user** message of `tool_result` blocks, each carrying the `tool_use_id` it answers:

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01A09q90qw90lq917835lq9",
      "content": "shipped, DHL, tracking DHL-992"
    }
  ]
}
```

Rules that get tested:

- The id must match, or the model cannot pair result to request.
- Results for parallel tool calls go in **one** user message, not several.
- A failed tool still returns a `tool_result`, with `is_error: true`. Dropping it strands the turn.
- Execute the tool but forget to append the result, and the next request carries no new information. The model reasons only over the message list.

---

## 3. Error response — real capture

*Source: genuinely captured in this repo on 31 Aug 2026 by sending an invalid key via `reference/raw-http.sh`.*

```json
{
  "type": "error",
  "error": {
    "type": "authentication_error",
    "message": "API key is invalid."
  },
  "request_id": null
}
```

HTTP status was **401**. Two lessons:

- Errors are a different top-level shape — `type: "error"`, no `content`, no `stop_reason`. Code that reaches straight for `response.content` throws on the error path.
- `curl` exited **0** on this 401. The failure lost its failure-ness crossing the boundary, which is **Domain 5.3, error propagation**. See the `case` block in `raw-http.sh` for the fix, and note which statuses are retryable (429, 5xx) versus terminal (other 4xx).

---

## 4. The loop, as a table

| `stop_reason` | Meaning | Your code does |
|---|---|---|
| `"tool_use"` | Claude wants tools run | Execute **every** `tool_use` block, append all `tool_result`s in one user message, call again |
| `"end_turn"` | Finished | Present the final text |
| `"max_tokens"` | Cut off mid-thought | **Not** done. Handle as incomplete — raise `max_tokens` or retry |
| `"stop_sequence"` | Hit a stop sequence | Not done either |
| `"refusal"` | Safety classifier declined | Check `stop_details.category`. Read before touching `content` |
| `"pause_turn"` | Long-running server tool paused | Send the turn back to continue it |

The completion condition is **`stop_reason`**. Never `content[0].type`, never parsing prose for "I'm done", never an iteration count. A loop cap is a safety fuse, not a completion rule.

---

## Practise without a key

Write the JSON by hand and have it marked in chat. Useful drills:

1. An assistant message that calls two tools in parallel, plus the single user message answering both.
2. The same, where one tool failed.
3. Trace what `content` and `stop_reason` look like across all four turns of the ORD-8841 example in [1.1-agentic-loops.md](../../domains/01-agentic-architecture/1.1-agentic-loops.md).

Hand-writing these is closer to what the exam asks than running working code is.
