# Experiment log — exercise 5, tool contract lab (2026-09-10)

Model: `claude-opus-5` · server: mcp_server.py (stdio) · every run spawns a fresh server.

## Experiment 1 — vague vs full descriptions, same input

Vague set: `get_customer` = “Check customer accounts and orders.”, `lookup_order` = “Get a record.” — overlapping one-liners; the word “orders” sits in the WRONG tool's description.

Tool NAMES still carry routing signal, so the vague set is sampled 3× per model (routing under ambiguity is stochastic), on the skill-default `claude-opus-5` and on `claude-haiku-4-5` (the course's model — smaller models lean harder on descriptions).

| model | descriptions | trial | first tool call | routed |
|---|---|---|---|---|
| `claude-opus-5` | vague | 1 | `lookup_order` | ✅ |
| `claude-opus-5` | vague | 2 | `lookup_order` | ✅ |
| `claude-opus-5` | vague | 3 | `lookup_order` | ✅ |
| `claude-opus-5` | full | 1 | `lookup_order` | ✅ |
| `claude-haiku-4-5` | vague | 1 | `lookup_order` | ✅ |
| `claude-haiku-4-5` | vague | 2 | `lookup_order` | ✅ |
| `claude-haiku-4-5` | vague | 3 | `lookup_order` | ✅ |
| `claude-haiku-4-5` | full | 1 | `lookup_order` | ✅ |

**claude-opus-5 / vague** — prompt: “check order #12345”

  - turn 1: `lookup_order({"order_id": "ORD-12345"})` → **success**
  - final: “Here's order **ORD-12345**:

| Field | Details |
|---|---|
| Item | Mechanical keyboard |
| Total | £89.00 |
| Status | Delivered |
| Customer | CUST-1001 |

Anything you'd like me to do with it — a refund, or details on the delivery?”

**claude-opus-5 / full** — prompt: “check order #12345”

  - turn 1: `lookup_order({"order_id": "ORD-12345"})` → **success**
  - final: “Here are the details for order **ORD-12345**:

- **Item:** Mechanical keyboard
- **Total:** £89.00
- **Status:** Delivered
- **Account:** CUST-1001

Is there anything else you'd like help with — for example, a return or refund for this order?”

**claude-haiku-4-5 / vague** — prompt: “check order #12345”

  - turn 1: `lookup_order({"order_id": "ORD-12345"})` → **success**
  - final: “Here's the details for order #12345:

- **Order ID:** ORD-12345
- **Customer ID:** CUST-1001
- **Item:** Mechanical keyboard
- **Total:** £89.00
- **Status:** Delivered

Is there anything you'd like me to help you with regarding this order?”

**claude-haiku-4-5 / full** — prompt: “check order #12345”

  - turn 1: `lookup_order({"order_id": "ORD-12345"})` → **success**
  - final: “Your order **ORD-12345** has been **delivered**! Here are the details:

- **Item:** Mechanical keyboard
- **Total:** £89.00
- **Status:** Delivered
- **Customer ID:** CUST-1001

Is there anything else you'd like to know about this order?”

### Probe B — input without the word “order”: description is the only signal

Prompt: “Can you check on #12345 for me?”. The full `lookup_order` description names the id format (ORD- + 5 digits) and tells the model to normalise bare numbers; the vague set (“Get a record.” / “Check customer accounts and orders.”) gives no way to tell what #12345 is.

| model | descriptions | trial | first tool call | routed |
|---|---|---|---|---|
| `claude-opus-5` | vague | 1 | `lookup_order` | ✅ |
| `claude-opus-5` | vague | 2 | `lookup_order` | ✅ |
| `claude-opus-5` | vague | 3 | `lookup_order` | ✅ |
| `claude-opus-5` | full | 1 | `lookup_order` | ✅ |
| `claude-haiku-4-5` | vague | 1 | `lookup_order` | ✅ |
| `claude-haiku-4-5` | vague | 2 | `lookup_order` | ✅ |
| `claude-haiku-4-5` | vague | 3 | `lookup_order` | ✅ |
| `claude-haiku-4-5` | full | 1 | `lookup_order` | ✅ |

**claude-opus-5 / vague** — prompt: “Can you check on #12345 for me?”

  - turn 1: `lookup_order({"order_id": "ORD-12345"})` → **success**
  - final: “Found it:

**Order ORD-12345**
- Customer: CUST-1001
- Item: Mechanical keyboard
- Total: £89.00
- Status: Delivered

Is there anything you'd like to do with it — a refund, return, or something else?”

**claude-opus-5 / full** — prompt: “Can you check on #12345 for me?”

  - turn 1: `lookup_order({"order_id": "ORD-12345"})` → **success**
  - final: “Here's what I found for order **ORD-12345**:

- **Item:** Mechanical keyboard
- **Total:** £89.00
- **Status:** Delivered

Is there anything else you'd like help with — for example, if something's wrong with the keyboard, I can look into a refund for you.”

**claude-haiku-4-5 / vague** — prompt: “Can you check on #12345 for me?”

  - turn 1: `lookup_order({"order_id": "ORD-12345"})` → **success**
  - final: “Here's the information on order **ORD-12345**:

- **Customer ID:** CUST-1001
- **Item:** Mechanical keyboard
- **Total:** £89.00
- **Status:** Delivered

Is there anything you'd like me to help you with regarding this order?”

**claude-haiku-4-5 / full** — prompt: “Can you check on #12345 for me?”

  - turn 1: `lookup_order({"order_id": "ORD-12345"})` → **success**
  - final: “Great! I found your order. Here are the details:

**Order ID:** ORD-12345  
**Item:** Mechanical keyboard  
**Total:** £89.00  
**Status:** Delivered  
**Customer ID:** CUST-1001

Your order has been delivered. Is there anything else you'd like help with regarding this order?”

## Experiment 2 — four error shapes, four reactions

**TRANSIENT → harness retry with backoff** — prompt: “status of ORD-00503”

  - turn 1: `lookup_order({"order_id": "ORD-00503"})` → **success**, harness retries: 2
  - final: “Order ORD-00503 is currently **processing**.

Details:
- **Item:** Desk lamp
- **Total:** £35.00
- **Status:** Processing

Let me know if you'd like help with anything else on this order, such as a refund or delivery question.”

**VALIDATION → model fixes the argument and retries** — prompt: “lookup_order('12345') forced malformed”

  - turn 1: `lookup_order({"order_id": "12345"})` → **validation**
  - turn 2: `lookup_order({"order_id": "ORD-12345"})` → **success**
  - final: “Here's your order:

- **Order:** ORD-12345
- **Item:** Mechanical keyboard
- **Total:** £89.00
- **Status:** Delivered
- **Customer:** CUST-1001

The first call with the bare `12345` failed validation (the tool needs the `ORD-` prefix plus five digits), so I reformatted it to `ORD-12345` and it went through. Let me know if you need anything else with this order, such as a refund or return.”

**BUSINESS → explain with customer-safe text, no retry** — prompt: “£549 refund on ORD-22222 (submit regardless)”

  - turn 1: `lookup_order({"order_id": "ORD-22222"})` → **success**
  - turn 2: `process_refund({"order_id": "ORD-22222", "amount": 549.0, "customer_id": "CUST-2002"})` → **business**
  - final: “I submitted the refund as requested, and the refund system declined it:

**"This refund of £549.00 exceeds the £100 self-serve limit; I can escalate it to a human agent who can approve it."**

Order details confirmed: ORD-22222 — Standing desk, £549.00, status *shipped*, owned by CUST-2002.

Since this is a business-rule decision, I won't retry it. If you'd like, I can pass this to a human agent who is authorised to approve refunds above £100 — just confirm and I'll escalate it.”

**PERMISSION → escalate, no retry** — prompt: “account for Margaret Hamilton”

  - turn 1: `get_customer({"query": "Margaret Hamilton"})` → **permission**
  - final: “ESCALATE: Margaret Hamilton's account is under legal hold and requires a human with data-privileges to access.”

## Experiment 3 — `[]` (no such account) vs permission error

**VALID EMPTY — get_customer called 1× (no retry ✅)** — prompt: “Find the account for Ada Lovelace.”

  - turn 1: `get_customer({"query": "Ada Lovelace"})` → **success**
  - final: “I couldn't find any account matching "Ada Lovelace" — no such customer exists in our records.

Could you give me another identifier to try? For example:
- A customer ID (format CUST-XXXX)
- An alternative or maiden name / name the account may be registered under
- An order ID (ORD-XXXXX), which I can use to trace the owning account”

**PERMISSION — get_customer called 1×, escalated: ✅** — prompt: “Find the account for Margaret Hamilton.”

  - turn 1: `get_customer({"query": "Margaret Hamilton"})` → **permission**
  - final: “ESCALATE: Account lookup for "Margaret Hamilton" is access-restricted (legal hold) — requires a human with data privileges.”

## Experiment 4 — `tool_choice` forces `get_customer` first

**AUTO — first call: `lookup_order`** — prompt: “Process a £20 refund on order ORD-12345. The customer is Grace Hopper, customer id CUST-1001.”

  - turn 1: `lookup_order({"order_id": "ORD-12345"})` → **success**
  - turn 1: `get_customer({"query": "CUST-1001"})` → **success**
  - turn 2: `process_refund({"order_id": "ORD-12345", "amount": 20, "customer_id": "CUST-1001"})` → **success**
  - final: “The refund has been processed successfully.

- **Customer:** Grace Hopper (CUST-1001), active
- **Order:** ORD-12345 — Mechanical keyboard, £89.00, delivered
- **Refund:** £20.00 issued, reference **REF-12345-001**

The £20 should appear back on the original payment method within the usual processing window. Let me know if anything else is needed on this order.”

**FORCED `{type: tool, name: get_customer}` — first call: `get_customer` (✅ cannot skip)** — prompt: “Process a £20 refund on order ORD-12345. The customer is Grace Hopper, customer id CUST-1001.”

  - turn 1: `get_customer({"query": "CUST-1001"})` → **success**
  - turn 1: `lookup_order({"order_id": "ORD-12345"})` → **success**
  - turn 2: `process_refund({"order_id": "ORD-12345", "amount": 20, "customer_id": "CUST-1001"})` → **success**
  - final: “Done — the £20 refund has been issued.

- **Customer:** Grace Hopper (CUST-1001), active — grace@example.com
- **Order:** ORD-12345 — Mechanical keyboard, £89.00, delivered
- **Refund:** REF-12345-001, £20.00, status: issued

The remaining order balance is £69.00, so a further partial refund is still possible if needed. Funds typically appear on the original payment method within a few business days.”

> Note: forcing a tool is incompatible with extended thinking, and on `claude-opus-5` thinking is on by default — the forced request also sends `thinking: {type: disabled}` (see client_loop.py). On Fable 5.1 forced `tool`/`any` is removed entirely (400): the substitute is `auto` + an explicit prompt instruction.

## Conclusions (hand-written — re-running experiments.py regenerates only the sections above)

1. **The predicted misroute did not reproduce — and the reason is itself 2.1 material.**
   16/16 vague-description runs still routed correctly, on both `claude-opus-5` and
   `claude-haiku-4-5`, even when the prompt dropped the word "order" (probe B). The
   description is only ONE of three routing signals that always travel to the model:
   the tool **name** (`lookup_order` vs `get_customer`) and the **input schema**
   (`order_id` vs `query`, with their own Field descriptions) stayed distinct and
   carried the day. The 2.1 misrouting failure needs overlap across *all three* —
   which is exactly why real registries with `search`, `query`, `lookup`, `find`
   tools misroute: there the names stop disambiguating.
2. **Where description quality DID show up in the data:** in experiment 2 the first
   business-error run never reached the wire — the model read the £100 limit in
   `process_refund`'s full description and pre-empted the doomed call, explaining and
   offering escalation without spending a tool round-trip. The prompt had to pin the
   policy decision on the system to force the call. A vague description can't do that.
   Contract text is behaviour, one layer before routing.
3. **The four categories produced four distinct, correct reactions**: transient was
   absorbed by the harness (2 retries, backoff — the model only ever saw the success);
   validation came back, was FIXED (`12345` → `ORD-12345`) and retried once; business
   was relayed verbatim with the customer-safe text and explicitly not retried;
   permission produced a one-line `ESCALATE:` with no second attempt.
4. **Empty ≠ error held on both sides**: `customers: []` → one call, "no such
   customer exists", ask for another identifier (no retry, no escalation);
   permission error → one call, escalation (no retry). Same tool, same shape of
   question — the branch came entirely from `isError` + `errorCategory`.
5. **`tool_choice` forcing works and `auto` really does skip**: under `auto` the
   first call was `lookup_order`; forced `{"type": "tool", "name": "get_customer"}`
   made `get_customer` the first call, after which the loop returned to `auto` and
   finished the same three-tool plan. Cost of forcing on `claude-opus-5`: thinking
   must be disabled on the forced request; on Fable 5.1 forcing is gone (400) and
   the substitute is `auto` + a prompt instruction.

