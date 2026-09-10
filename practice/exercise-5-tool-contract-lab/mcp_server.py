"""Support-desk MCP server — practice exercise 5 (Domain 2 tool contract lab).

Same shape as academy/course-c-claude-api/mcp-project/mcp_server.py: a
FastMCP stdio server where @mcp.tool + type hints + pydantic Field generate
the JSON schema. Everything here exercises the CONTRACTS, not a backend —
the data is a hand-rolled in-memory dict.

What this file demonstrates (maps to docs/exercises.md #5):

1. Three tools: get_customer / lookup_order / process_refund.
2. TWO description sets, chosen by the TOOL_DESCRIPTIONS env var:
     - "vague": one-line, overlapping descriptions on the get_customer /
       lookup_order pair (the deliberate misrouting trap from 2.1).
     - "full" (default): purpose, inputs, examples, edges, boundaries.
   The env var is what the ${ENV_VAR} in .mcp.json expands into, so the
   config artefact and the experiment share one mechanism.
3. All FOUR error categories from 2.2 on the wire, as STRUCTURED payloads
   (isError / errorCategory / isRetryable / message) rather than raised
   exceptions. Raising would also cross MCP as an error result
   (CallToolResult.isError=True), but a bare string forces the agent to
   guess the category — the whole point of 2.2 is that the category is
   DATA the caller can branch on.
4. The exam-favourite distinction: a lookup that ran and matched nothing
   is a SUCCESS with an empty body (isError: false, customers: []),
   never an error. Only a query that could not run (or must not run) is
   an error.

Run: TOOL_DESCRIPTIONS=full SUPPORT_DESK_API_KEY=dummy python mcp_server.py
"""

import os
import sys

from pydantic import Field

# SDK-drift compat: in the Python MCP SDK 2.x, FastMCP was renamed to
# MCPServer (mcp.server.mcpserver). The decorator surface we use —
# @mcp.tool(name=..., description=...) with pydantic Field defaults and
# mcp.run(transport="stdio") — is the same in both, so one aliased import
# keeps this file runnable under the course venv (mcp 1.x) AND the repo
# root venv (mcp 2.x, the one .mcp.json points at).
try:
    from mcp.server.fastmcp import FastMCP  # mcp 1.x (course project era)
except (ImportError, ModuleNotFoundError):
    from mcp.server.mcpserver import MCPServer as FastMCP  # mcp 2.x rename

# ---------------------------------------------------------------------------
# Config from the environment — this is the .mcp.json ${ENV_VAR} story.
#
# SUPPORT_DESK_API_KEY stands in for a real backend credential. It is NEVER
# hardcoded here and never committed in .mcp.json; the config file carries
# "${SUPPORT_DESK_API_KEY}" and Claude Code (or our experiment harness)
# injects the real value at spawn time. We fail fast if it is missing so a
# broken expansion is loud, not a silent auth failure three tools deep.
# ---------------------------------------------------------------------------
API_KEY = os.environ.get("SUPPORT_DESK_API_KEY")
if not API_KEY:
    print(
        "support-desk: SUPPORT_DESK_API_KEY is not set. "
        "Export it (any value works for this lab) or fix the ${ENV_VAR} "
        "expansion in .mcp.json.",
        file=sys.stderr,
    )
    sys.exit(1)

# "vague" reproduces the misrouting trap; anything else gets the full set.
DESCRIPTION_SET = os.environ.get("TOOL_DESCRIPTIONS", "full").lower()

# mcp 1.x FastMCP takes log_level; 2.x MCPServer does not — pass name only.
mcp = FastMCP("support-desk")

# ---------------------------------------------------------------------------
# In-memory dataset. Fake on purpose — the contracts are what is exercised.
#
# CUST-9999 is flagged restricted (think: legal hold / GDPR erasure request)
# so get_customer on it produces a PERMISSION error: the record exists, the
# query could run, but this caller must not see it. Contrast with a name
# that simply matches nothing, which is a SUCCESSFUL empty result.
# ---------------------------------------------------------------------------
CUSTOMERS = {
    "CUST-1001": {
        "customer_id": "CUST-1001",
        "name": "Grace Hopper",
        "email": "grace@example.com",
        "status": "active",
        "restricted": False,
    },
    "CUST-2002": {
        "customer_id": "CUST-2002",
        "name": "Alan Turing",
        "email": "alan@example.com",
        "status": "active",
        "restricted": False,
    },
    "CUST-9999": {
        "customer_id": "CUST-9999",
        "name": "Margaret Hamilton",
        "email": "margaret@example.com",
        "status": "active",
        "restricted": True,  # legal hold: permission error, not "not found"
    },
}

ORDERS = {
    "ORD-12345": {
        "order_id": "ORD-12345",
        "customer_id": "CUST-1001",
        "item": "Mechanical keyboard",
        "total": 89.00,
        "status": "delivered",
    },
    "ORD-22222": {
        "order_id": "ORD-22222",
        "customer_id": "CUST-2002",
        "item": "Standing desk",
        "total": 549.00,
        "status": "shipped",
    },
    # ORD-00503 simulates a flaky upstream: the first two lookups "time out"
    # (transient error), the third succeeds. Lets the client loop PROVE its
    # retry-with-backoff policy actually recovers.
    "ORD-00503": {
        "order_id": "ORD-00503",
        "customer_id": "CUST-2002",
        "item": "Desk lamp",
        "total": 35.00,
        "status": "processing",
    },
}

# Refunds above this need a human — the BUSINESS error trigger.
REFUND_POLICY_LIMIT = 100.00

# Per-process call counter for the simulated flaky upstream.
_flaky_calls = {"ORD-00503": 0}


# ---------------------------------------------------------------------------
# The 2.2 error contract, as two tiny helpers.
#
# Minimum payload from domains/02-tool-design-mcp/2.2-structured-errors.md:
#   isError, errorCategory, isRetryable, human-readable message,
#   what was attempted (we carry it in `attempted`).
#
# The category names the agent's NEXT MOVE:
#   transient  -> retry with backoff, then propagate
#   validation -> fix the input (or ask the user), then retry
#   business   -> do NOT retry; explain with the customer-safe text
#   permission -> do NOT retry with the same credentials; escalate
# ---------------------------------------------------------------------------
def ok(**body):
    """A successful result. Note: an EMPTY successful result still goes
    through here — empty is not an error."""
    return {"isError": False, **body}


def err(category: str, message: str, retryable: bool, attempted: str):
    """A structured error. `message` must be safe to show a customer on
    business errors — silent isRetryable:false with no text makes the
    agent invent a reason (2.2)."""
    return {
        "isError": True,
        "errorCategory": category,  # transient | validation | business | permission
        "isRetryable": retryable,
        "message": message,
        "attempted": attempted,
    }


# ---------------------------------------------------------------------------
# Description sets. The VAGUE pair is the 2.1 trap: both one-liners talk
# about "checking" and "records", and get_customer's even mentions orders —
# so "check order #12345" plausibly routes to get_customer. The FULL set
# states purpose, inputs, an example, edge behaviour, and the boundary with
# the sibling tool ("use lookup_order for order status, not this").
# ---------------------------------------------------------------------------
DESCRIPTIONS = {
    "vague": {
        "get_customer": "Check customer accounts and orders.",
        "lookup_order": "Get a record.",
    },
    "full": {
        "get_customer": (
            "Search customer ACCOUNTS by customer id (e.g. 'CUST-1001') or by "
            "(partial) name. Returns a JSON list of matching customer records "
            "(customer_id, name, email, status). An empty list means no such "
            "customer exists — that is a definitive answer, not a failure; do "
            "not retry it. Restricted accounts return a permission error. This "
            "tool knows nothing about orders: for order status or details, use "
            "lookup_order instead."
        ),
        "lookup_order": (
            "Fetch one ORDER by its order id. Order ids look like 'ORD-12345' "
            "(the literal prefix 'ORD-' plus exactly five digits) — if the user "
            "gives a bare number like '#12345', normalise it to 'ORD-12345' "
            "before calling. Returns the order's item, total, status and owning "
            "customer_id, or order: null when no order has that id (a definitive "
            "answer — do not retry). Use this for 'where is my order / check "
            "order X' questions; for account questions use get_customer."
        ),
    },
}
# process_refund keeps ONE full description in both sets: the exercise says
# to make one PAIR ambiguous, and the refund tool is the control.
PROCESS_REFUND_DESCRIPTION = (
    "Issue a refund for an order. Requires order_id (format 'ORD-' + 5 "
    "digits), the refund amount in the order's currency (must be > 0 and "
    "<= the order total), and the customer_id that owns the order. Refunds "
    f"above the self-serve policy limit (£{REFUND_POLICY_LIMIT:.0f}) are "
    "rejected as a business-rule error and must be escalated to a human — "
    "do not retry those. Look the order up first if you are unsure of any "
    "field."
)


def _describe(tool_name: str) -> str:
    """Pick the active description for a tool, falling back to full."""
    active = DESCRIPTIONS.get(DESCRIPTION_SET, DESCRIPTIONS["full"])
    return active.get(tool_name, DESCRIPTIONS["full"][tool_name])


# ---------------------------------------------------------------------------
# Tool 1: get_customer
# ---------------------------------------------------------------------------
@mcp.tool(name="get_customer", description=_describe("get_customer"))
def get_customer(
    query: str = Field(description="Customer id (CUST-XXXX) or full/partial name"),
):
    q = query.strip().lower()

    # Permission gate BEFORE the search results leak anything: a restricted
    # match is 'you may not', never 'does not exist'. Lying with [] here
    # would send the agent down the "no such account" path — wrong move,
    # because a human CAN handle this account.
    for cust in CUSTOMERS.values():
        if cust["restricted"] and (
            q == cust["customer_id"].lower() or q in cust["name"].lower()
        ):
            return err(
                category="permission",
                message=(
                    "This account is access-restricted (legal hold). The "
                    "support agent role cannot view it; escalate to a human "
                    "with data-privileges."
                ),
                retryable=False,  # retrying with the same credentials cannot succeed
                attempted=f"get_customer(query={query!r})",
            )

    matches = [
        {k: v for k, v in cust.items() if k != "restricted"}
        for cust in CUSTOMERS.values()
        if not cust["restricted"]
        and (q == cust["customer_id"].lower() or q in cust["name"].lower())
    ]

    # THE distinction 2.2 drills: the query RAN and found nothing, so this
    # is a success with an empty list. isError stays false. The agent's
    # correct reaction is "no such account", not a retry, not a page.
    return ok(customers=matches)


# ---------------------------------------------------------------------------
# Tool 2: lookup_order
# ---------------------------------------------------------------------------
@mcp.tool(name="lookup_order", description=_describe("lookup_order"))
def lookup_order(
    order_id: str = Field(description="Order id, format ORD-XXXXX (5 digits)"),
):
    oid = order_id.strip().upper()

    # VALIDATION error: the input is malformed, so the query never ran.
    # Retryable — but only AFTER the caller fixes the argument. The message
    # tells the agent exactly how to fix it (2.1: edges belong in the
    # contract, and error text is part of the contract).
    if not (oid.startswith("ORD-") and oid[4:].isdigit() and len(oid) == 9):
        return err(
            category="validation",
            message=(
                f"Malformed order id {order_id!r}: expected the literal "
                "prefix 'ORD-' followed by exactly five digits, e.g. "
                "'ORD-12345'. Fix the id and call again."
            ),
            retryable=True,
            attempted=f"lookup_order(order_id={order_id!r})",
        )

    # TRANSIENT error: simulated upstream timeout on ORD-00503, twice, then
    # recovery. Real cause would be a 503/timeout; the contract is the same:
    # isRetryable true, so the CLIENT LOOP (not the model) backs off and
    # retries before anything reaches the conversation.
    if oid in _flaky_calls:
        _flaky_calls[oid] += 1
        if _flaky_calls[oid] <= 2:
            return err(
                category="transient",
                message=(
                    "Upstream order service timed out (simulated 503). "
                    "Safe to retry with backoff."
                ),
                retryable=True,
                attempted=f"lookup_order(order_id={oid!r})",
            )

    order = ORDERS.get(oid)
    # Well-formed id, query ran, nothing matched: SUCCESS with a null body.
    # Same rule as the empty customer list — 'no such order' is an answer.
    if order is None:
        return ok(order=None, note=f"No order with id {oid} exists.")

    return ok(order=order)


# ---------------------------------------------------------------------------
# Tool 3: process_refund
# ---------------------------------------------------------------------------
@mcp.tool(name="process_refund", description=PROCESS_REFUND_DESCRIPTION)
def process_refund(
    order_id: str = Field(description="Order id, format ORD-XXXXX"),
    amount: float = Field(description="Refund amount, > 0, <= order total"),
    customer_id: str = Field(description="Customer that owns the order, CUST-XXXX"),
):
    oid = order_id.strip().upper()
    cid = customer_id.strip().upper()

    # VALIDATION: bad amount — the request never reached business logic.
    if amount <= 0:
        return err(
            category="validation",
            message=f"Refund amount must be positive; got {amount}.",
            retryable=True,
            attempted=f"process_refund({oid}, {amount}, {cid})",
        )

    order = ORDERS.get(oid)
    if order is None:
        return err(
            category="validation",
            message=(
                f"Unknown order id {oid!r}. Verify it with lookup_order "
                "before requesting a refund."
            ),
            retryable=True,
            attempted=f"process_refund({oid}, {amount}, {cid})",
        )

    # PERMISSION: refunds against a restricted account are off-limits to
    # this role regardless of amount.
    owner = CUSTOMERS.get(order["customer_id"])
    if owner and owner["restricted"]:
        return err(
            category="permission",
            message=(
                "The owning account is access-restricted; refunds on it "
                "require a human with elevated privileges."
            ),
            retryable=False,
            attempted=f"process_refund({oid}, {amount}, {cid})",
        )

    if cid != order["customer_id"]:
        return err(
            category="validation",
            message=(
                f"Order {oid} belongs to {order['customer_id']}, not {cid}. "
                "Check the customer id and try again."
            ),
            retryable=True,
            attempted=f"process_refund({oid}, {amount}, {cid})",
        )

    # BUSINESS: policy says no. The input is valid, the system is healthy,
    # retrying can never change the outcome — so isRetryable is false AND
    # the message is customer-safe text the agent can relay verbatim.
    # (2.2: silent false with no text makes the agent invent a reason.)
    if amount > REFUND_POLICY_LIMIT:
        return err(
            category="business",
            message=(
                f"This refund of £{amount:.2f} exceeds the "
                f"£{REFUND_POLICY_LIMIT:.0f} self-serve limit; I can "
                "escalate it to a human agent who can approve it."
            ),
            retryable=False,
            attempted=f"process_refund({oid}, {amount}, {cid})",
        )

    if amount > order["total"]:
        return err(
            category="business",
            message=(
                f"Refund £{amount:.2f} exceeds the order total "
                f"£{order['total']:.2f}; the maximum refundable amount is "
                f"£{order['total']:.2f}."
            ),
            retryable=False,
            attempted=f"process_refund({oid}, {amount}, {cid})",
        )

    # Happy path: fake refund id, no real money anywhere.
    return ok(
        refund_id=f"REF-{oid[4:]}-001",
        order_id=oid,
        amount=amount,
        status="issued",
    )


if __name__ == "__main__":
    # stdio transport: the client owns this process and speaks JSON-RPC over
    # stdin/stdout — same as the course project and .mcp.json stdio servers.
    mcp.run(transport="stdio")
