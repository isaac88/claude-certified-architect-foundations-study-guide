---
description: Report the next unticked study step from progress.md
allowed-tools: Read
---

Read `progress.md` at the repo root. Steps are markdown checkboxes of the form
`- [ ] NN. <description>` grouped under phase headings.

Report, in this order and nothing else:

1. The first unticked step (its number and full line), and the phase it sits in.
2. Any unticked step with a LOWER number than a ticked one (a skipped step) — name it
   and note that skipping was either deliberate (check the line for a note) or a gap.
3. One line: what sitting this implies next.

Do not summarise the whole file, do not list completed steps, do not edit anything.
