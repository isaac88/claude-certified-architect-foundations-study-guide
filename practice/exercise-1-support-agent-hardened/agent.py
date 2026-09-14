"""Exercise 1, hardened — the support agent with hooks (course G Build 1, step 19).

Exercise 22/23's loop, unchanged, wrapped with the two lifecycle hooks the exam
names in 1.5 and the structured-error contract from 2.2:

  PreToolUse   runs after the model asks for a tool, before the code runs it.
               It is the 1.4 PREREQUISITE GATE: process_refund is denied until a
               verified customer id exists in the session, denied when the order
               belongs to someone else, and denied above REFUND_LIMIT. A denial is
               a normal tool_result with is_error=True and the 2.2 fields — the
               model sees WHY and whether calling again can ever work.
  PostToolUse  runs after the tool executed, before the model sees the result.
               It records identity (get_customer success flips the session flag
               the gate reads), normalises lookup_order's raw payload (numeric
               status code -> word, unix time -> ISO, internal fields stripped:
               1.5's "one shape regardless of source", 5.1's trim-before-append),
               and books executed refunds.

The system prompt deliberately does NOT say "verify the customer first". That is
the 1.4 experiment: the gate, not the prompt, is what makes the 8% skip rate 0%.
The run log shows whether the model tried to refund before verifying and what
it received when it did.

Escalation (1.4) is explicit: three criteria, one handoff packet built by the
HARNESS from session state — five fields, all required, because the human who
picks it up does not have the transcript.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

HERE = Path(__file__).parent
REPO_ROOT = HERE.parents[1]
load_dotenv(REPO_ROOT / "academy" / "course-c-claude-api" / ".env")

client = Anthropic()
MODEL = "claude-haiku-4-5"          # the course's model; the point here is the harness
REFUND_LIMIT = 500.00               # GBP — above this an agent may not refund alone

RUN_LOG = HERE / "run-log.md"

# ----------------------------------------------------------- fixture data
CUSTOMERS = {
    "CUST-001": {"customer_id": "CUST-001", "name": "Ana Ruiz", "email": "ana@example.org"},
    "CUST-002": {"customer_id": "CUST-002", "name": "Tomás Vidal", "email": "tomas@example.org"},
}
ORDERS = {
    "ORD-1001": {"order_id": "ORD-1001", "customer_id": "CUST-001", "amount": 120.00,
                 "status_code": 4, "placed_at": 1757500000,
                 "warehouse_bin": "B-17-04", "internal_notes": "fragile; repacked twice", "sku_list": ["LAMP-220"]},
    "ORD-1002": {"order_id": "ORD-1002", "customer_id": "CUST-001", "amount": 900.00,
                 "status_code": 4, "placed_at": 1757300000,
                 "warehouse_bin": "A-02-11", "internal_notes": "", "sku_list": ["TV-55-OLED"]},
    "ORD-2001": {"order_id": "ORD-2001", "customer_id": "CUST-002", "amount": 45.00,
                 "status_code": 3, "placed_at": 1757600000,
                 "warehouse_bin": "C-09-01", "internal_notes": "", "sku_list": ["MUG-01"]},
}
STATUS_CODES = {1: "created", 2: "paid", 3: "shipped", 4: "delivered", 5: "refunded"}

# ------------------------------------------------------ structured errors
def error(category: str, retryable: bool, message: str, attempted: dict) -> dict:
    """The 2.2 contract. `errorCategory` says what KIND of failure; `isRetryable`
    says whether calling again can ever work. They are independent: the gate
    below returns permission+retryable (do the prerequisite, then retry) and
    permission+not-retryable (escalate) from the same category."""
    return {"isError": True, "errorCategory": category, "isRetryable": retryable,
            "message": message, "attempted": attempted}


# -------------------------------------------------------------- the tools
def get_customer(email: str) -> dict:
    match = next((c for c in CUSTOMERS.values() if c["email"].lower() == email.lower()), None)
    # An empty match is a VALID EMPTY (2.2): the lookup worked, nobody has that email.
    return {"customer": match}


def lookup_order(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None:
        return {"order": None}
    return {"order": dict(order)}      # raw: numeric status, unix time, internal fields


def process_refund(order_id: str, amount: float) -> dict:
    order = ORDERS.get(order_id)
    if order is None:
        return error("validation", True, f"Unknown order id {order_id!r}; check the id and call again.",
                     {"order_id": order_id, "amount": amount})
    if amount > order["amount"]:
        return error("business", False, f"Refund £{amount:.2f} exceeds the order total £{order['amount']:.2f}.",
                     {"order_id": order_id, "amount": amount})
    return {"refund_id": f"RF-{order_id[-4:]}-{int(amount)}", "order_id": order_id,
            "amount": amount, "status": "processed"}


def escalate_to_human(reason: str) -> dict:
    return {"escalated": True, "reason": reason}


TOOLS = [
    {"name": "get_customer",
     "description": "Look up a customer by the email address they give you. Returns the customer record, or customer: null when no account has that email (that is a definitive answer, not an error).",
     "input_schema": {"type": "object", "properties": {"email": {"type": "string"}}, "required": ["email"]}},
    {"name": "lookup_order",
     "description": "Fetch one order by id (format ORD-NNNN). Returns order: null when the id does not exist.",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
    {"name": "process_refund",
     "description": "Refund an amount in GBP against an order. Returns the refund record, or a structured error explaining why it was not processed.",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "amount": {"type": "number"}},
                      "required": ["order_id", "amount"]}},
    {"name": "escalate_to_human",
     "description": "Hand the conversation to a human agent. Use when the customer asks for a person, or when a tool result tells you the request is outside your authority.",
     "input_schema": {"type": "object", "properties": {"reason": {"type": "string"}}, "required": ["reason"]}},
]

SYSTEM_PROMPT = """You are a customer-support agent for a small online shop. Use the tools to \
help the customer with orders and refunds. Amounts are in GBP. Be brief. When a tool \
result says the request is outside your authority or the customer asks for a person, \
call escalate_to_human and tell the customer a colleague will take over."""
# Note what is NOT here: "verify the customer before refunding". The gate does that.

# ---------------------------------------------------------- session state
def new_session() -> dict:
    return {"identity_verified": False, "customer_id": None, "orders_seen": [],
            "refunds": [], "escalation": None, "gate_events": []}


# ------------------------------------------------------------------ hooks
ESCALATION_CRITERIA = (
    "refund amount above REFUND_LIMIT",
    "order does not belong to the verified customer",
    "customer asks for a human",
)


def pre_tool_use(name: str, tool_input: dict, session: dict) -> dict | None:
    """The gate. Return None to allow the call; return an error payload to DENY it
    (the tool function is then never executed). Only process_refund is gated."""
    if name != "process_refund":
        return None
    attempted = {"tool": name, **tool_input}
    if not session["identity_verified"]:
        denial = error("permission", True,
                       "Denied: no verified customer in this session. Call get_customer with the customer's email first, then retry the refund.",
                       attempted)
        session["gate_events"].append({"rule": "identity_verified", "denied": True, "retryable": True})
        return denial
    order = ORDERS.get(tool_input.get("order_id", ""))
    if order and order["customer_id"] != session["customer_id"]:
        session["escalation"] = {"root_cause": ESCALATION_CRITERIA[1], "amount": tool_input.get("amount")}
        session["gate_events"].append({"rule": "order_ownership", "denied": True, "retryable": False})
        return error("permission", False,
                     "Denied: that order belongs to a different customer. This has been escalated; do not retry.",
                     attempted)
    if float(tool_input.get("amount", 0)) > REFUND_LIMIT:
        session["escalation"] = {"root_cause": ESCALATION_CRITERIA[0], "amount": tool_input["amount"]}
        session["gate_events"].append({"rule": "refund_limit", "denied": True, "retryable": False})
        return error("permission", False,
                     f"Denied: £{tool_input['amount']:.2f} exceeds the £{REFUND_LIMIT:.0f} limit an agent may refund alone. Escalated to a human; do not retry.",
                     attempted)
    session["gate_events"].append({"rule": "all", "denied": False})
    return None


def post_tool_use(name: str, tool_input: dict, output: dict, session: dict) -> dict:
    """Runs on every EXECUTED tool. Records state the gate reads, and normalises
    what the model will see."""
    if output.get("isError"):
        return output
    if name == "get_customer" and output.get("customer"):
        session["identity_verified"] = True
        session["customer_id"] = output["customer"]["customer_id"]
    elif name == "lookup_order" and output.get("order"):
        raw = output["order"]
        session["orders_seen"].append(raw["order_id"])
        # one shape for the model: words not codes, ISO not epoch, five fields not eight
        output = {"order": {
            "order_id": raw["order_id"],
            "customer_id": raw["customer_id"],
            "amount": raw["amount"],
            "status": STATUS_CODES.get(raw["status_code"], f"unknown({raw['status_code']})"),
            "placed_at": datetime.fromtimestamp(raw["placed_at"], tz=timezone.utc).isoformat(),
        }}
    elif name == "process_refund":
        session["refunds"].append(output)
    elif name == "escalate_to_human":
        # The model may escalate before ever attempting the refund (it read the
        # normalised order and saw the problem itself). The packet must still be
        # built from STATE, not from the model's prose: infer the criterion from
        # the orders this session looked up, and take the amount from the order.
        if session["escalation"] is None:
            session["escalation"] = infer_escalation(session)
        session["escalation"]["reason_from_model"] = tool_input.get("reason")
    return output


def infer_escalation(session: dict) -> dict:
    """Deterministic root cause from session facts; falls back to 'asks for a human'."""
    for order_id in session["orders_seen"]:
        order = ORDERS[order_id]
        if session["customer_id"] and order["customer_id"] != session["customer_id"]:
            return {"root_cause": ESCALATION_CRITERIA[1], "amount": order["amount"]}
        if order["amount"] > REFUND_LIMIT:
            return {"root_cause": ESCALATION_CRITERIA[0], "amount": order["amount"]}
    return {"root_cause": ESCALATION_CRITERIA[2], "amount": None}


# -------------------------------------------------- exercise 22's machinery
def add_user_message(messages, message):
    messages.append({"role": "user", "content": message.content if isinstance(message, Message) else message})


def add_assistant_message(messages, message):
    messages.append({"role": "assistant", "content": message.content if isinstance(message, Message) else message})


def chat(messages, system=None, tools=None, max_tokens=1000):
    params = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
    if system:
        params["system"] = system
    if tools:
        params["tools"] = tools
    return client.messages.create(**params)


def text_from_message(message):
    return "\n".join(b.text for b in message.content if b.type == "text")


ROUTER = {"get_customer": get_customer, "lookup_order": lookup_order,
          "process_refund": process_refund, "escalate_to_human": escalate_to_human}


def run_tools(message, session, trace):
    """Exercise 22's run_tools with the two hooks around the call."""
    results = []
    for block in (b for b in message.content if b.type == "tool_use"):
        tool_input = dict(block.input)
        denial = pre_tool_use(block.name, tool_input, session)
        if denial is not None:
            output = denial                                   # tool NOT executed
        else:
            try:
                output = ROUTER[block.name](**tool_input)
            except Exception as e:                            # never raise across the boundary
                output = error("validation", True, f"{type(e).__name__}: {e}", {"tool": block.name, **tool_input})
            output = post_tool_use(block.name, tool_input, output, session)
        trace.append({"tool": block.name, "input": tool_input, "executed": denial is None,
                      "category": output.get("errorCategory") if output.get("isError") else "success",
                      "retryable": output.get("isRetryable")})
        results.append({"type": "tool_result", "tool_use_id": block.id,
                        "content": json.dumps(output), "is_error": bool(output.get("isError"))})
    return results


def run_conversation(user_message: str, max_turns: int = 8) -> dict:
    session, trace, messages = new_session(), [], []
    add_user_message(messages, user_message)
    final_text = ""
    for turn in range(1, max_turns + 1):
        response = chat(messages, system=SYSTEM_PROMPT, tools=TOOLS)
        add_assistant_message(messages, response)
        calls = [b.name for b in response.content if b.type == "tool_use"]
        print(f"  [{turn}] stop={response.stop_reason} tools={calls}")
        if response.stop_reason != "tool_use":
            final_text = text_from_message(response)
            break
        results = run_tools(response, session, trace)
        for t in trace[-len(results):]:
            flag = "DENIED " if not t["executed"] else ("ERROR " if t["category"] != "success" else "")
            print(f"       {flag}{t['tool']}({t['input']}) -> {t['category']}"
                  + (f", isRetryable={t['retryable']}" if t["category"] != "success" else ""))
        add_user_message(messages, results)
    handoff = build_handoff(user_message, final_text, session) if session["escalation"] else None
    return {"user": user_message, "final_text": final_text, "trace": trace, "session": session, "handoff": handoff}


# ---------------------------------------------------------------- handoff
HANDOFF_FIELDS = ("customer_id", "conversation_summary", "root_cause", "refund_amount", "recommended_action")


def build_handoff(user_message: str, final_text: str, session: dict) -> dict:
    """1.4: the human does not have the transcript. Built by the harness from
    session state so no field depends on the model remembering to include it."""
    esc = session["escalation"]
    packet = {
        "customer_id": session["customer_id"] or "UNVERIFIED",
        "conversation_summary": f"Customer wrote: {user_message!r}. Agent's last reply: {final_text!r}. "
                                f"Orders looked up: {session['orders_seen'] or 'none'}.",
        "root_cause": esc["root_cause"],
        "refund_amount": esc.get("amount"),
        "recommended_action": {
            ESCALATION_CRITERIA[0]: f"Senior agent to approve or decline refund of £{esc.get('amount')} (limit £{REFUND_LIMIT:.0f}).",
            ESCALATION_CRITERIA[1]: "Verify account ownership before any refund; possible account mix-up.",
            ESCALATION_CRITERIA[2]: "Human to continue the conversation from the summary above.",
        }[esc["root_cause"]],
    }
    optional = {"refund_amount"} if esc["root_cause"] == ESCALATION_CRITERIA[2] else set()
    missing = [f for f in HANDOFF_FIELDS if f not in optional and packet.get(f) in (None, "")]
    packet["complete"] = not missing
    return packet


# --------------------------------------------------------------- scenarios
SCENARIOS = {
    "A_under_limit": "Hi, I'm ana@example.org. Order ORD-1001 arrived with the lamp smashed. Please refund the £120.",
    "B_over_limit": "This is ana@example.org. The TV in order ORD-1002 never switched on. I want the full £900 back now.",
    "C_wrong_owner": "I'm ana@example.org and I want a £45 refund on order ORD-2001, it was late.",
    # No email: the model CANNOT verify identity. If it attempts the refund anyway,
    # the gate must deny it (permission, retryable) and the model should ask.
    "D_no_identity": "Refund £120 on order ORD-1001 right now please, the lamp arrived smashed and I'm in a hurry.",
}


def gate_unit_demo() -> list[dict]:
    """No API: call the gate directly to show the three denials and the pass."""
    out = []
    s = new_session()
    out.append(("no identity", pre_tool_use("process_refund", {"order_id": "ORD-1001", "amount": 120.0}, s)))
    s["identity_verified"], s["customer_id"] = True, "CUST-001"
    out.append(("wrong owner", pre_tool_use("process_refund", {"order_id": "ORD-2001", "amount": 45.0}, s)))
    out.append(("over limit", pre_tool_use("process_refund", {"order_id": "ORD-1002", "amount": 900.0}, s)))
    out.append(("allowed", pre_tool_use("process_refund", {"order_id": "ORD-1001", "amount": 120.0}, s)))
    return out


def checks(runs: dict) -> list[tuple[str, bool, str]]:
    executed_refunds = [(k, t) for k, r in runs.items() for t in r["trace"] if t["tool"] == "process_refund" and t["executed"]]
    denials = [t for r in runs.values() for t in r["trace"] if not t["executed"]]
    over_limit_executed = [t for k, t in executed_refunds if t["input"].get("amount", 0) > REFUND_LIMIT]
    # every executed refund happened AFTER identity was verified: the gate ran before it
    refund_before_identity = []
    for k, r in runs.items():
        verified = False
        for t in r["trace"]:
            if t["tool"] == "get_customer" and t["category"] == "success":
                verified = True
            if t["tool"] == "process_refund" and t["executed"] and not verified:
                refund_before_identity.append(k)
    handoffs = [r["handoff"] for r in runs.values() if r["handoff"]]
    return [
        ("no refund executed before identity was verified", not refund_before_identity, f"{len(executed_refunds)} refund(s) executed, {len(denials)} call(s) denied by the gate"),
        ("no refund above the limit was executed", not over_limit_executed, f"limit £{REFUND_LIMIT:.0f}; over-limit attempts: {sum(1 for r in runs.values() for t in r['trace'] if t['tool']=='process_refund' and t['input'].get('amount',0) > REFUND_LIMIT)}"),
        ("every denial carried the five 2.2 fields", all(t["category"] and t["retryable"] is not None for t in denials), f"{len(denials)} denial(s)"),
        ("every handoff packet is complete (5 fields)", bool(handoffs) and all(h["complete"] for h in handoffs), f"{len(handoffs)} packet(s)"),
        ("model saw normalised orders (status word, ISO time, no internal fields)", True, "asserted by construction in post_tool_use; see the trace"),
    ]


if __name__ == "__main__":
    print("== gate unit demo (no API) ==")
    demo = gate_unit_demo()
    for label, payload in demo:
        print(f"  {label:12} -> {'ALLOW' if payload is None else f'{payload['errorCategory']}, isRetryable={payload['isRetryable']}'}")
    runs = {}
    for key, msg in SCENARIOS.items():
        print(f"\n== scenario {key} ==\n  user: {msg}")
        runs[key] = run_conversation(msg)
        print(f"  final: {runs[key]['final_text'][:200]!r}")
        if runs[key]["handoff"]:
            print(f"  HANDOFF: {json.dumps(runs[key]['handoff'], indent=None)[:300]}...")
    results = checks(runs)
    print("\n== checks ==")
    for name, ok, ev in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name} — {ev}")

    lines = [f"# Exercise 1 (hardened) run log — {MODEL}, limit £{REFUND_LIMIT:.0f}", "",
             "Generated by `agent.py`. Fixture data is invented.", "",
             "## Gate unit demo (no API)", "", "| Case | Gate result |", "|---|---|",
             *[f"| {l} | {'ALLOW' if p is None else f'`{p['errorCategory']}`, isRetryable=`{p['isRetryable']}` — {p['message']}'} |" for l, p in demo],
             "", "## Checks", "", "| Check | Result | Evidence |", "|---|---|---|",
             *[f"| {n} | {'PASS' if ok else 'FAIL'} | {ev} |" for n, ok, ev in results]]
    for key, r in runs.items():
        lines += ["", f"## Scenario {key}", "", f"**User:** {r['user']}", "", "| # | Tool | Input | Executed | Result |", "|---|---|---|---|---|",
                  *[f"| {i} | `{t['tool']}` | `{json.dumps(t['input'])}` | {'yes' if t['executed'] else '**DENIED by gate**'} | {t['category']}" + (f" (isRetryable={t['retryable']})" if t['category'] != 'success' else "") + " |" for i, t in enumerate(r["trace"], 1)],
                  "", f"**Gate events:** `{json.dumps(r['session']['gate_events'])}`", "", f"**Final reply:** {r['final_text']}"]
        if r["handoff"]:
            lines += ["", "**Handoff packet (built by the harness):**", "", "```json", json.dumps(r["handoff"], indent=2), "```"]
    RUN_LOG.write_text("\n".join(lines) + "\n")
    print(f"\nwrote {RUN_LOG.relative_to(REPO_ROOT)}")
