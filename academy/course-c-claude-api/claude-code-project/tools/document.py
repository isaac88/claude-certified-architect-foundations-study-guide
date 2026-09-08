"""Course C — exercise 45 (Claude Code block): document tools.

WHAT THIS TEACHES — the lesson's Claude Code workflows, run for real on this
starter: /init produced ../CLAUDE.md; then context -> plan -> implement as TDD:
tests for document_path_to_markdown were written FIRST (red: ImportError),
then this implementation, then registration in main.py (green, 6/6).

SOURCE — https://anthropic.skilljar.com/claude-with-the-anthropic-api/287805
EXAM LINK — D3: Claude Code as the client; CLAUDE.md as standing context.
RUN — from claude-code-project/: `uv sync` once, then `uv run pytest`.

NOTES FROM THE COURSE — binary_document_to_markdown is the starter's code,
untouched; the exercise adds only what the lesson's plan lists.
"""

import os

from markitdown import MarkItDown, StreamInfo
from io import BytesIO
from pydantic import Field


def binary_document_to_markdown(binary_data: bytes, file_type: str) -> str:
    """Converts binary document data to markdown-formatted text."""
    md = MarkItDown()
    file_obj = BytesIO(binary_data)
    stream_info = StreamInfo(extension=file_type)
    result = md.convert(file_obj, stream_info=stream_info)
    return result.text_content


def document_path_to_markdown(
    file_path: str = Field(description="Path to the document file to convert"),
) -> str:
    """Convert a document file on disk to markdown-formatted text.

    Validates that the file exists, determines its type from the file
    extension, reads the binary data, and converts it to markdown using
    binary_document_to_markdown.

    When to use:
    - When the document is available on the local filesystem and you have its path
    - Supports the formats markitdown handles (e.g. docx, pdf)

    When not to use:
    - When you already hold the document's bytes — use binary_document_to_markdown

    Examples:
    >>> document_path_to_markdown("tests/fixtures/mcp_docs.docx")
    '# Model Context Protocol...'
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    file_type = os.path.splitext(file_path)[1].lstrip(".")
    with open(file_path, "rb") as f:
        binary_data = f.read()
    return binary_document_to_markdown(binary_data, file_type)
