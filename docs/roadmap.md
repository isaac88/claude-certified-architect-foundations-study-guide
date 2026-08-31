# Roadmap — course C and the domains, interleaved

Written 31 Aug 2026, from the real position: course C finished through *Structured data exercise*, domain step 6 not yet done.

This is the **execution order**. [study-steps.md](study-steps.md) still owns the numbering that [../progress.md](../progress.md) ticks; this file says what to do on which day and what to pair it with.

---

## The rule

**One sitting = one course section + one domain file.**

Never a course section alone. The course teaches the vendor's happy path; the domain files teach the decisions, traps and anti-patterns the exam actually tests. Four times already the course has taught something the current API rejects — `temperature`, assistant prefill, `content[0].text`, schema cardinality. Course alone means learning wrong answers.

**Practice sets are gates, not milestones.** Below target, re-read the missed files before moving on. That is the whole point of the *Prompt evaluation* section applied to yourself.

---

## Phase A — unblock Domain 1 (do this first)

Domain 1 is **27%** — the largest domain on the exam, and the one the notes warn hardest about: *if Domain 1 is weak, you do not pass*. The course saves it for its final teaching section. Do not wait for that.

- [ ] **A1.** Read `domains/01-agentic-architecture/1.1-agentic-loops.md` to the end of *Exam traps*. Answer the premature-stop question in chat. *(= step 6)*

Ten minutes. Everything else in Domain 1 builds on it.

---

## Phase B — Domain 1 in parallel with Prompt evaluation

Course section: **Prompt evaluation** (7 lessons + quiz). Domain files: the rest of Domain 1.

| | Course lesson | Domain file |
|---|---|---|
| B1 | Prompt evaluation | `1.2-multi-agent-orchestration.md` |
| B2 | A typical eval workflow | `1.3-subagent-invocation.md` |
| B3 | Generating test datasets | `1.4-workflow-enforcement.md` |
| B4 | Running the eval | `1.5-sdk-hooks.md` |
| B5 | Model based grading | `1.6-task-decomposition.md` |
| B6 | Code based grading | `1.7-session-state.md` |
| B7 | Exercise on prompt evals + quiz | — |

- [ ] **B8. GATE:** `domains/01-agentic-architecture/practice.md` — target **8/10**. Below that, re-read the missed files before Phase C.
- [ ] **B9.** Exercise 1 in `docs/exercises.md` — support agent with a real loop and a refund gate. *(= step 14)*

---

## Phase C — Domain 4 with Prompt engineering

Course section: **Prompt engineering techniques**. Domain 4 is **20%**, and this is its natural pair.

| | Course lesson | Domain file |
|---|---|---|
| C1 | Prompt engineering / Being clear and direct | `4.1-explicit-criteria.md` |
| C2 | Being specific | `4.2-few-shot.md` |
| C3 | Structure with XML tags | `4.3-structured-output.md` |
| C4 | Providing examples | `4.4-validation-retry.md` |
| C5 | Exercise on prompting | `4.5-batch-processing.md` |
| C6 | Quiz on prompt engineering | `4.6-multi-pass-review.md` |

- [ ] **C7. GATE:** Domain 4 `practice.md` — target **7/8**.
- [ ] **C8.** Exercise 3 — schema + few-shot + validation-retry over 10 documents. *(= step 25)*

---

## Phase D — Domain 2 with Tool use and MCP

Course sections: **Tool use with Claude** (12 lessons), then **Model Context Protocol** (12 lessons). Domain 2 is **18%**.

| | Course lesson | Domain file |
|---|---|---|
| D1 | Introducing tool use → Tool schemas | `2.1-tool-interfaces.md` |
| D2 | Handling message blocks → Sending tool results | `2.2-structured-errors.md` |
| D3 | Multi-turn with tools → Using multiple tools | *(re-read `1.1` — this is the loop)* |
| D4 | Fine grained tool calling, text edit, web search | `2.5-built-in-tools.md` |
| D5 | Introducing MCP → Defining tools with MCP | `2.3-tool-distribution.md` |
| D6 | Resources, prompts, client implementation | `2.4-mcp-integration.md` |

- [ ] **D7. GATE:** Domain 2 `practice.md` — target **6/7**.
- [ ] **D8.** Exercise 5 in `docs/exercises.md`. *(= step 16)*

---

## Phase E — Domain 5 with Features of Claude

Course section: **Features of Claude**. Domain 5 is **15%** and maps closely: caching, citations/provenance, extended thinking, context limits.

| | Course lesson | Domain file |
|---|---|---|
| E1 | Extended thinking | `5.1-preserve-critical-info.md` |
| E2 | Image / PDF support | `5.2-escalation.md` |
| E3 | Citations | `5.6-provenance.md` |
| E4 | Prompt caching + rules of caching | `5.4-large-codebases.md` |
| E5 | Prompt caching in action | `5.3-error-propagation.md` |
| E6 | Code execution and the Files API | `5.5-human-review.md` |

- [ ] **E7. GATE:** Domain 5 `practice.md` — target **5/6**.

---

## Phase F — Domain 3 with Claude Code

Course section: **Anthropic apps — Claude Code and computer use** (4 lessons). Domain 3 is **20%** but the course covers it thinly, so lean on the domain files here.

| | Course lesson | Domain file |
|---|---|---|
| F1 | Anthropic apps / Claude Code setup | `3.1-claude-md.md` |
| F2 | Claude Code in action | `3.2-commands-and-skills.md` |
| F3 | Enhancements with MCP servers | `3.3-path-specific-rules.md` |
| F4 | — | `3.4-plan-mode.md` |
| F5 | — | `3.5-iterative-refinement.md` |
| F6 | — | `3.6-cicd.md` |

- [ ] **F7. GATE:** Domain 3 `practice.md` — target **7/8**.
- [ ] **F8.** Exercise 2 — hierarchy, glob rules, forked skill, CI `-p` + JSON. *(= step 22)*

---

## Phase G — Agents and workflows (Domain 1 revision)

Course section: **Agents and workflows** (7 lessons + quiz). By now this is revision, which is the intent — you will have done Domain 1 six weeks earlier.

- [ ] **G1.** Parallelization / chaining / routing workflows — check against `1.6-task-decomposition.md`
- [ ] **G2.** Agents and tools / environment inspection — check against `1.2`, `1.3`
- [ ] **G3.** Workflows vs agents — check against `1.4-workflow-enforcement.md` and `cheatsheets/decision-rules.md`
- [ ] **G4.** Quiz on agents and workflows
- [ ] **G5.** Course **final assessment**

Anything the course contradicts, trust the domain files and log it in the course README divergence table.

---

## Phase H — lock it together

- [ ] **H1.** Exercise 4 — research pipeline. *(= step 26)*
- [ ] **H2.** Recite `cheatsheets/decision-rules.md` from memory. Mark gaps against `cheatsheets/anti-patterns.md`. *(= step 27)*
- [ ] **H3. GATE:** `practice/mixed-set.md` — target **10/12**. *(= step 28)*
- [ ] **H4.** Official Anthropic Academy practice exam. *(= step 29)*
- [ ] **H5.** Re-read only the task files you missed. No new topics. *(= step 30)*
- [ ] **H6.** Book the exam.

---

## Deliberately skipped

**RAG and Agentic Search** (7 lessons). Checked against the blueprint: no domain file covers it, and it is not a named exam domain. Good engineering knowledge, zero marks. **Skim the videos, write no exercises.**

Courses **D (Bedrock)** and **E (GCP)** — the exam is not cloud-specific.

---

## Sequencing rationale

| Decision | Why |
|---|---|
| Domain 1 before everything | 27% — the heaviest domain, and the course covers it last |
| Domain 4 second | 20%, and the course's two prompt sections pair with it directly |
| Domain 3 late | 20%, but the course only gives it 4 lessons — the domain files carry it, so it does not need to wait for them |
| RAG dropped | 0% of the exam |
| Practice sets as gates | The *Prompt evaluation* lesson applied to yourself: no measurement, no idea |

## Daily rule

One course section, one domain file, two check questions, tick `progress.md`, stop. Do not double up to "catch up" — the gates will tell you if you are behind.

## Exam week

`cheatsheets/decision-rules.md` and `cheatsheets/anti-patterns.md` only. No new material. Sleep.
