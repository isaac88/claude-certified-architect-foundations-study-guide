---
paths:
  - "**/tests/**/*.py"
  - "**/test_*.py"
---

# Test files

- pytest, one behaviour per test, named for the behaviour (`test_missing_file_returns_empty_list`), not the function.
- Tests never call the live API. Inputs come from fixtures under the project's `tests/fixtures/`; in `claude-code-project` those fixtures are gitignored course assets — a fresh clone needs `app_starter.zip` re-downloaded before the suite is green.
- TDD when the task says so: write the failing test first, run it red, then implement; never edit a test to make it pass.
- Run the suite from the project's own environment (`uv run pytest` in the course projects, `.venv/bin/python -m pytest` elsewhere) and paste the pass count into the commit message.
