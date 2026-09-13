# Course C folder — conventions that differ from the rest of the repo

- Exercise files: `exercises/NN-<course-section-in-kebab-case>.py`, one per course section, with the five-part docstring header (WHAT THIS TEACHES, SOURCE, EXAM LINK, RUN, NOTES FROM THE COURSE) described in `README.md`. Add an index row in `README.md` for every new file.
- Scope discipline: an exercise covers what its course section covers. Later or outside material goes in `reference/` and the exercise links to it.
- Instructor-vs-current-API divergences are recorded once, in the `README.md` divergence table. Check it before re-verifying anything.
- Eval and grader code runs on `claude-haiku-4-5`: Opus spends the whole `max_tokens` budget on thinking and returns no text. Prefill + `stop_sequences` is used where the lesson uses it and works on Haiku only; Opus/Sonnet 5 return 400.
- Never score an ungraded case as 0; exclude it and report it.
- `mcp-project/` and `claude-code-project/` each have their OWN environment from the shipped lock (anthropic 0.51.0 era); run them from their folder, not with the root `.venv`. `claude-code-project` needs no API key — Claude Code is the client.
- `.env` here holds `ANTHROPIC_API_KEY` and `CLAUDE_MODEL`; `load_dotenv` finds it by walking up from any exercise.
