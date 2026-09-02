"""
Exercise 25 — the text edit tool.

Course C, section: "The text edit tool" (Tool Use block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    (paste the section URL here)
    Code from the official 005_text_editor_tool.ipynb.
    Tool versions: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/text-editor-tool

WHAT THIS TEACHES
    An ANTHROPIC-DEFINED tool: the schema lives on Anthropic's side, so the
    request carries only a stub —
        {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"}
    — and Claude expands it into the full editor specification (commands:
    view, str_replace, create, insert; view_range; and so on). What does
    NOT come for free is the implementation: every command still arrives
    as an ordinary tool_use block, and WE write the code that touches the
    filesystem. Split brain: their schema, our hands.

    The tool_use input is {"command": "view"|"str_replace"|"create"|
    "insert", "path": ..., + command-specific args}; the router dispatches
    on command instead of tool name. The loop from exercise 22 is
    untouched — an Anthropic-defined tool is just a tool.

TWO BUGS/DIVERGENCES WORTH THE PRICE OF THE LESSON
    - THE NOTEBOOK'S ROUTER IS BROKEN: it matches tool_name ==
      "str_replace_editor" (the pre-Claude-4 name) while its own schema
      registers "str_replace_based_edit_tool". Every call would bounce as
      "Unknown tool name", is_error=True. Fixed here; recorded because it
      is the third silent-name-mismatch bug this course has shipped
      (exercise 12's {task}, exercise 15's {prompt_inputs_spec}).
    - The lesson page's version stubs are for claude-3-5/3-7-sonnet, both
      retired. Current pairing (per the docs link above, verified live):
      text_editor_20250728 + str_replace_based_edit_tool for Claude 4+.
      undo_edit exists only in the older 20241022/20250124 versions — the
      notebook implements it, current Claude cannot ask for it.

SANDBOXING — the part the notebook got half right
    The notebook HAS a path guard (_validate_path rejects paths that
    escape base_dir — the model's "path" is untrusted input, and "../../
    .ssh/config" is one hallucination away). But it defaults base_dir to
    os.getcwd(), which from this repo's root would hand the model the
    whole repository. Here base_dir is pinned to exercises/25-workdir/,
    wiped and reseeded on every run, so the experiment is repeatable and
    the blast radius is one directory.

EXAM LINK
    D2 — Anthropic-defined vs user-defined tools: who owns the schema vs
    who owns the execution. D2/security — validate model-supplied paths
    BEFORE touching the filesystem; the guard is a gate, not a prompt
    instruction (1.4 again). D1 — same loop, no changes: tool variety
    scales without touching orchestration.

RUN
    From the repo root (wipes and reseeds exercises/25-workdir/):
        .venv/bin/python academy/course-c-claude-api/exercises/25-the-text-edit-tool.py

    MEASURED 2 Sep 2026, claude-sonnet-4-5, two runs:

    RUN 1 — OUR bug, and a specimen of model error recovery. The tool was
    constructed before the sandbox reset, so rmtree deleted .backups/ and
    every str_replace failed with ENOENT (the backup copy). Watch what the
    model did with 5 consecutive is_error results: retried str_replace,
    tried create (FileExistsError), tried insert (sent malformed args),
    created test.py successfully, then STOPPED GRACEFULLY — pasted the
    main.py code into its text answer for the human to apply and said
    plainly it could not modify the file. Honest degradation, driven
    entirely by error-marked tool_results. (Contrast exercise 23's 'null':
    give the model real errors and it behaves; give it nothing and it
    invents success.)

    RUN 2 — happy path after the fix, 6 iterations:
        view(.) -> view(./main.py) -> str_replace(./main.py) ok
        -> create(./test.py) ok -> view(./main.py) -> end_turn

    VERIFIED beyond "files created": the generated suite passes —
        Ran 6 tests in 0.792s  OK
    One craft observation: the model sized the Taylor series at
    num_terms = 10**(digits+1) — a million terms where Machin's formula
    needs ~10. Correct result, ~100,000x the work. "Tests pass" and
    "well engineered" are different bars; only reading the code shows the
    second.
"""

import json
import os
import shutil
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-sonnet-4-5"      # the notebook's choice for this section

WORKDIR = Path(__file__).parent / "25-workdir"

SEED_MAIN_PY = '''\
"""A tiny utilities module used by exercise 25."""


def greet(name):
    return f"Hello, {name}!"


def circle_area(radius):
    PI = 3.14  # rough approximation
    return PI * radius ** 2
'''


def add_user_message(messages, message):
    messages.append({
        "role": "user",
        "content": message.content if isinstance(message, Message) else message,
    })


def add_assistant_message(messages, message):
    messages.append({
        "role": "assistant",
        "content": message.content if isinstance(message, Message) else message,
    })


def chat(messages, system=None, tools=None, max_tokens=2000):
    # 2000, not the notebook's 1000: a created test file plus commentary
    # can overrun 1000 and a truncated tool_use is a lost turn.
    params = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
    if system:
        params["system"] = system
    if tools:
        params["tools"] = tools
    return client.messages.create(**params)


def text_from_message(message):
    return "\n".join(b.text for b in message.content if b.type == "text")


# --------------------------------------- our implementation of their tool
class TextEditorTool:
    """The notebook's implementation, kept faithful except: base_dir is
    required (no cwd default), and the outer `except E: raise type(E)(...)`
    ceremony — a literal no-op — is dropped."""

    def __init__(self, base_dir):
        self.base_dir = str(base_dir)
        self.backup_dir = os.path.join(self.base_dir, ".backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def _validate_path(self, file_path):
        # The model chose this path. Treat it as hostile until proven
        # inside the sandbox — this line is what stops "../../.env".
        abs_path = os.path.normpath(os.path.join(self.base_dir, file_path))
        if not abs_path.startswith(self.base_dir):
            raise ValueError(
                f"Access denied: Path '{file_path}' is outside the allowed directory")
        return abs_path

    def _backup_file(self, file_path):
        if not os.path.exists(file_path):
            return ""
        os.makedirs(self.backup_dir, exist_ok=True)   # survive a sandbox reset
        backup_path = os.path.join(
            self.backup_dir,
            f"{os.path.basename(file_path)}.{os.path.getmtime(file_path):.0f}")
        shutil.copy2(file_path, backup_path)
        return backup_path

    def view(self, file_path, view_range=None):
        abs_path = self._validate_path(file_path)

        if os.path.isdir(abs_path):
            return "\n".join(os.listdir(abs_path))

        if not os.path.exists(abs_path):
            raise FileNotFoundError("File not found")

        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.read().split("\n")

        start, end = (view_range if view_range else (1, len(lines)))
        if end == -1:
            end = len(lines)

        # Line numbers in the output — the model addresses edits by line.
        return "\n".join(f"{i}: {line}"
                         for i, line in enumerate(lines[start - 1:end], start))

    def str_replace(self, file_path, old_str, new_str):
        abs_path = self._validate_path(file_path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError("File not found")

        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()

        match_count = content.count(old_str)
        if match_count == 0:
            raise ValueError(
                "No match found for replacement. Please check your text and try again.")
        elif match_count > 1:
            # Refusing ambiguous replacements forces the model to resend
            # with more surrounding context — same contract as Claude
            # Code's own Edit tool.
            raise ValueError(
                f"Found {match_count} matches for replacement text. "
                f"Please provide more context to make a unique match.")

        self._backup_file(abs_path)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content.replace(old_str, new_str))

        return "Successfully replaced text at exactly one location."

    def create(self, file_path, file_text):
        abs_path = self._validate_path(file_path)

        if os.path.exists(abs_path):
            raise FileExistsError("File already exists. Use str_replace to modify it.")

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(file_text)

        return f"Successfully created {file_path}"

    def insert(self, file_path, insert_line, new_str):
        abs_path = self._validate_path(file_path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError("File not found")

        self._backup_file(abs_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if lines and not lines[-1].endswith("\n"):
            new_str = "\n" + new_str

        if insert_line == 0:
            lines.insert(0, new_str + "\n")
        elif 0 < insert_line <= len(lines):
            lines.insert(insert_line, new_str + "\n")
        else:
            raise IndexError(
                f"Line number {insert_line} is out of range. "
                f"File has {len(lines)} lines.")

        with open(abs_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return f"Successfully inserted text after line {insert_line}"


# ------------------------------------------------- schema stub and router
def get_text_edit_schema(model):
    """The whole request-side schema. Claude expands the type string into
    the full tool spec server-side. (The lesson's claude-3-5/3-7 branches
    are retired; Claude 4+ uses this pairing.)"""
    return {
        "type": "text_editor_20250728",
        "name": "str_replace_based_edit_tool",
    }


def run_tool(tool_name, tool_input):
    # NOTEBOOK BUG FIXED: it matched "str_replace_editor" here while the
    # schema registered "str_replace_based_edit_tool" — every call errored.
    if tool_name == "str_replace_based_edit_tool":
        command = tool_input["command"]
        if command == "view":
            return text_editor_tool.view(tool_input["path"],
                                         tool_input.get("view_range"))
        elif command == "str_replace":
            return text_editor_tool.str_replace(
                tool_input["path"], tool_input["old_str"], tool_input["new_str"])
        elif command == "create":
            return text_editor_tool.create(tool_input["path"],
                                           tool_input["file_text"])
        elif command == "insert":
            return text_editor_tool.insert(
                tool_input["path"], tool_input["insert_line"],
                tool_input["new_str"])
        else:
            raise Exception(f"Unknown text editor command: {command}")
    else:
        raise Exception(f"Unknown tool name: {tool_name}")


def run_tools(message):
    tool_result_blocks = []
    for block in message.content:
        if block.type != "tool_use":
            continue
        command = block.input.get("command", "?")
        path = block.input.get("path", "?")
        try:
            tool_output = run_tool(block.name, block.input)
            print(f"    {command}({path}) -> ok", flush=True)
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(tool_output),
                "is_error": False,
            })
        except Exception as e:
            print(f"    {command}({path}) -> ERROR: {e}", flush=True)
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": f"Error: {e}",
                "is_error": True,
            })
    return tool_result_blocks


def run_conversation(messages):
    iteration = 0
    while True:
        iteration += 1
        response = chat(messages, tools=[get_text_edit_schema(MODEL)])
        print(f"[{iteration}] stop_reason={response.stop_reason}  "
              f"blocks={[b.type for b in response.content]}", flush=True)

        add_assistant_message(messages, response)
        if text := text_from_message(response):
            print(f"[{iteration}] {text}")

        if response.stop_reason != "tool_use":
            break

        add_user_message(messages, run_tools(response))

    return messages


# ------------------------------------------------------------------ run
# Fresh sandbox every run: repeatable experiment, bounded blast radius.
# The tool is constructed AFTER the reset — run 1's crash (see MEASURED)
# came from creating .backups/ first and rmtree-ing it a moment later.
shutil.rmtree(WORKDIR, ignore_errors=True)
WORKDIR.mkdir()
(WORKDIR / "main.py").write_text(SEED_MAIN_PY)
text_editor_tool = TextEditorTool(base_dir=WORKDIR)
print(f"sandbox: {WORKDIR} (seeded with main.py)\n")

messages = []
add_user_message(messages, (
    "Open the ./main.py file and write out a function to calculate pi to "
    "the 5th digit. Then create a ./test.py file to test your implementation."
))
run_conversation(messages)

print("\n--- files in the sandbox after the run:")
for path in sorted(WORKDIR.iterdir()):
    if path.name == ".backups":
        continue
    print(f"\n### {path.name}\n{path.read_text()}")

# NOTES FROM THE COURSE
# - Anthropic-defined tool: send the version-typed stub, Claude knows the
#   full schema. We still implement every command ourselves.
# - Commands: view (file or directory, optional view_range), str_replace,
#   create, insert. undo_edit only in pre-Claude-4 tool versions.
# - Line-numbered view output is what lets the model target insert/replace
#   operations precisely.
# - Why this exists when IDEs have AI built in: to embed file editing in
#   YOUR application, where you control the loop and the filesystem.
#
# WORTH KNOWING (Domain 2 / Domain 3)
# - The str_replace uniqueness rule (0 matches = error, >1 = error) is the
#   same contract Claude Code's Edit tool enforces — now you have built
#   the reason: without it, a replacement is ambiguous and silent.
# - _validate_path is a D2 security gate on untrusted model input. The
#   guard lives in code; a system-prompt "only edit files in this folder"
#   would be 1.4's probabilistic non-fix.
# - NOTHING here verified the generated code actually runs. The model
#   wrote main.py and test.py; whether test.py passes is unknown until
#   something executes it. "It created the files" is not "it works" —
#   that gap is what evals (ex. 10-14) and CI exist to close.
