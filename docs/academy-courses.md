# Official Anthropic Academy courses

These are the **free** Skilljar courses listed under “Prepare for this exam” on Anthropic Academy. They are the vendor path. This repo is for exam decision-rules and recall. Do both.

Most candidates complete the courses **in the order below**, then register. You are already registered; work the courses **in parallel** with the numbered domain steps. Tick them in [../progress.md](../progress.md).

Do **not** block Domain 1 on finishing every card. Pair the course with the domain it feeds.

## Course list (Academy order)

| # | Course | Level | Exam use | Pair with |
|---|---|---|---|---|
| A | **AI Fluency: Framework & Foundations** | 100 | Collaboration, ethics, safe use. Thin on architecture items. | Optional if you already work with AI daily |
| B | **Claude 101** | 100 | Product surface, everyday use. Not the Architect exam core. | Optional baseline |
| C | **[Building with the Claude API](https://anthropic.skilljar.com/claude-with-the-anthropic-api)** | 100–200 | Messages API, prompting, evals, **tool use, RAG, agents, production**. Highest overlap with D1 / D2 / D4 / D5 | **Phase 1** (and keep using it through 2 and 4) |
| D | **Claude with Amazon Bedrock** | 100–200 | Same patterns **on Bedrock**. Exam is not AWS-specific | Do **if** you deploy on Bedrock; skip if you do not |
| E | **Claude on Google Cloud** | 100–200 | Same patterns **on GCP**. Exam is not GCP-specific | Do **if** you deploy on GCP; skip if you do not |
| F | **Introduction to Model Context Protocol** | 200 | MCP servers/clients, tools, resources, prompts | **Phase 2** (Domain 2) |
| G | **Claude Code in Action** | 200 | Context, **hooks**, custom commands, **Agent SDK** | **Phase 3** (Domain 3) and Domain 1.5 |

Bedrock and Google Cloud teach the same architectural ideas as the API course on a different host. Pick **at most one** unless you actually run both.

## Suggested pairing (do not wait for 100% course completion)

| When you are on | Also sit |
|---|---|
| Steps 6–14 (Domain 1) | C — Building with the Claude API (agents, tool use) |
| Steps 15–16 (Domain 2) | F — Introduction to MCP |
| Steps 20–22 (Domain 3) | G — Claude Code in Action |
| Steps 23–25 (Domain 4) | C — prompt / tool-use / production chapters you skipped |
| Cloud deployment at work | D **or** E, not both by default |

A and B first only if Claude is new. If you already use Claude at work, start at **C**.
