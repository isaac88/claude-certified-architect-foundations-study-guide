"""Client loop for the support-desk MCP server — practice exercise 5.

Two layers, deliberately separated because the exam separates them:

1. MCPClient — protocol plumbing, same shape as
   academy/course-c-claude-api/mcp-project/mcp_client.py: spawn the server
   over stdio, initialize, list_tools, call_tool.

2. SupportAgent — the agentic loop (Domain 1.1) that drives Claude with the
   MCP tools. It loops on stop_reason == "tool_use", executes each tool_use
   block via MCP, and reacts to the 2.2 error categories the way the
   category says:

     transient  -> the HARNESS retries with backoff before the model ever
                   sees the failure (retries are mechanical, not clever —
                   don't spend model turns on them)
     validation -> goes back to the model as is_error; the model fixes the
                   argument (or asks the user) and calls again
     business   -> goes back as is_error; the model relays the customer-safe
                   message and does NOT retry (isRetryable: false)
     permission -> goes back as is_error; the system prompt makes the model
                   escalate ("ESCALATE:" prefix) instead of retrying

   A SUCCESSFUL empty result (customers: [] / order: null) is NOT an error:
   it goes back with is_error unset and the model answers "no such account".

Every run returns a trace (which tools ran, with what args, what category
came back, how many harness retries happened) so experiments.py can write
measured before/after notes instead of vibes.
"""

import asyncio
import json
import time
from contextlib import AsyncExitStack
from typing import Any, Optional

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# Skill default; also supports forced tool_choice, which Fable 5.1 removed
# (there, forced 'tool'/'any' returns a 400 — auto + prompt is the substitute).
MODEL = "claude-opus-5"

# How many times the harness silently re-runs a transient failure before
# giving up and letting the model see the last error. 2 retries + the
# original call = 3 attempts, which is exactly what ORD-00503 needs.
TRANSIENT_MAX_RETRIES = 2

SYSTEM_PROMPT = """You are a customer-support agent for a small shop.
Use the tools to answer; never invent order or customer data.

Error-handling policy (the tool results carry errorCategory):
- validation: fix the argument yourself if the fix is obvious (e.g. \
normalise an id format), otherwise ask the user. Then call the tool again.
- business: do NOT retry. Relay the tool's message to the customer and \
offer the stated alternative.
- permission: do NOT retry. Reply with a single line starting exactly with \
"ESCALATE:" followed by a one-line reason for the human queue.
- A successful lookup that returns an empty list or a null order means the \
record definitively does not exist. Never retry it and never escalate it; \
tell the user no such account/order was found and ask for another identifier.
"""


class MCPClient:
    """Thin stdio MCP client — spawn server, initialize, list/call tools.

    Same shape as the course project's mcp_client.py: an AsyncExitStack owns
    the transport + session lifetimes, and the class is an async context
    manager so `async with MCPClient(...)` tears everything down cleanly.
    """

    def __init__(self, command: str, args: list[str], env: Optional[dict] = None):
        self._command = command
        self._args = args
        self._env = env  # <- where SUPPORT_DESK_API_KEY / TOOL_DESCRIPTIONS land
        self._session: Optional[ClientSession] = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    async def connect(self):
        server_params = StdioServerParameters(
            command=self._command, args=self._args, env=self._env
        )
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read, write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self._session.initialize()

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError("Not connected — call connect() first.")
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        return (await self.session().list_tools()).tools

    async def call_tool(self, name: str, tool_input: dict) -> types.CallToolResult:
        return await self.session().call_tool(name, tool_input)

    async def cleanup(self):
        await self._exit_stack.aclose()
        self._session = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


def mcp_tools_to_anthropic(tools: list[types.Tool]) -> list[dict]:
    """Translate MCP tool metadata into Anthropic `tools` entries.

    This is the whole trick behind 'MCP integration' when you own the loop:
    an MCP Tool already carries name / description / JSON schema, and the
    Messages API wants name / description / input_schema. Nothing is lost,
    nothing is added — which is WHY vague descriptions poison routing: the
    description travels verbatim from the server into the model's context.
    """
    return [
        {
            "name": t.name,
            "description": t.description or "",
            # mcp 1.x calls the field inputSchema (wire name); 2.x renamed
            # the Python attribute to input_schema. Same JSON either way.
            "input_schema": getattr(t, "input_schema", None) or t.inputSchema,
        }
        for t in tools
    ]


def parse_payload(result: types.CallToolResult) -> dict:
    """Extract our structured JSON payload from an MCP CallToolResult.

    FastMCP serialises the dict our tools return into a TextContent block.
    We parse it back so the harness can branch on errorCategory. A payload
    that is not JSON (shouldn't happen here) is wrapped as an opaque error.
    """
    text = ""
    for block in result.content:
        if isinstance(block, types.TextContent):
            text = block.text
            break
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {
            "isError": True,
            "errorCategory": "transient",
            "isRetryable": False,
            "message": f"Unparseable tool payload: {text[:200]!r}",
        }


class SupportAgent:
    """The agentic loop: Claude decides, this class executes over MCP."""

    def __init__(self, mcp_client: MCPClient, model: str = MODEL):
        self.client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        self.mcp = mcp_client
        self.model = model

    async def _call_with_retry_policy(self, name: str, args: dict) -> tuple[dict, int]:
        """Execute one tool call, applying the TRANSIENT retry policy.

        Returns (payload, retries_used). Only `transient` + isRetryable
        results are retried here — retrying validation/business/permission
        at the harness level would burn attempts on failures that can only
        be fixed by changing the input (validation) or can never succeed
        (business/permission). That branching IS the value of the category
        field.
        """
        retries = 0
        while True:
            payload = parse_payload(await self.mcp.call_tool(name, args))
            is_transient = (
                payload.get("isError")
                and payload.get("errorCategory") == "transient"
                and payload.get("isRetryable")
            )
            if not is_transient or retries >= TRANSIENT_MAX_RETRIES:
                return payload, retries
            retries += 1
            # Linear backoff is enough for a lab; production wants
            # exponential + jitter. The point is: the WAIT happens here,
            # in code, not by asking the model to "please wait".
            time.sleep(0.3 * retries)

    async def run(
        self,
        user_message: str,
        tool_choice: Optional[dict] = None,
        max_turns: int = 8,
    ) -> dict:
        """Drive one conversation to completion. Returns a trace dict:

        {
          "tool_calls": [{"turn", "tool", "input", "category", "retries"}...],
          "final_text": str,
          "turns": int,
        }
        """
        tools = mcp_tools_to_anthropic(await self.mcp.list_tools())
        messages: list[dict] = [{"role": "user", "content": user_message}]
        trace: dict[str, Any] = {"tool_calls": [], "final_text": "", "turns": 0}

        for turn in range(max_turns):
            trace["turns"] = turn + 1
            params: dict[str, Any] = {
                "model": self.model,
                "max_tokens": 4096,
                "system": SYSTEM_PROMPT,
                "tools": tools,
                "messages": messages,
            }
            # Forced tool_choice is incompatible with extended thinking, and
            # on claude-opus-5 thinking is ON by default (adaptive). So when
            # we force the first call we must explicitly disable thinking —
            # this interaction is itself exam material. The force applies to
            # the FIRST request only: once the forced call has happened, the
            # model needs "auto" back to pick its own next steps.
            if tool_choice is not None and turn == 0:
                params["tool_choice"] = tool_choice
                params["thinking"] = {"type": "disabled"}

            response = self.client.messages.create(**params)

            # end of the loop: the model stopped asking for tools.
            if response.stop_reason != "tool_use":
                trace["final_text"] = "".join(
                    b.text for b in response.content if b.type == "text"
                )
                return trace

            # Execute EVERY tool_use block in this assistant turn, then send
            # ALL results back in ONE user message — splitting them across
            # messages silently teaches the model to stop parallel calls.
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                payload, retries = await self._call_with_retry_policy(
                    block.name, dict(block.input)
                )
                trace["tool_calls"].append(
                    {
                        "turn": turn + 1,
                        "tool": block.name,
                        "input": dict(block.input),
                        "category": payload.get("errorCategory")
                        if payload.get("isError")
                        else "success",
                        "retries": retries,
                    }
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(payload),
                        # is_error mirrors the payload: an ACCESS FAILURE is
                        # an error; an empty match list is not. Setting
                        # is_error on "customers: []" is exactly the bug 2.2
                        # warns about (the agent then retries forever or
                        # pages a human about a non-problem).
                        "is_error": bool(payload.get("isError")),
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        trace["final_text"] = "(max_turns reached without end_turn)"
        return trace


async def smoke_test():
    """Connect, list tools, run one happy-path question. For `python client_loop.py`."""
    import os
    import sys
    from pathlib import Path

    server = Path(__file__).parent / "mcp_server.py"
    env = {
        **os.environ,
        "SUPPORT_DESK_API_KEY": os.environ.get("SUPPORT_DESK_API_KEY", "lab-dummy"),
        "TOOL_DESCRIPTIONS": "full",
    }
    async with MCPClient(command=sys.executable, args=[str(server)], env=env) as mcp_client:
        agent = SupportAgent(mcp_client)
        trace = await agent.run("What's the status of order ORD-12345?")
        print(json.dumps(trace, indent=2))


if __name__ == "__main__":
    asyncio.run(smoke_test())
