---
description: Audit an MCP server and repository for legibility on connect — what a cold agent gets, and how much it must already know
---

Run the legibility audit described in `skills/legibility-audit/SKILL.md` against $ARGUMENTS
(default: the current repository).

Do the static halves first — `probe_connect.py` and `inventory_repo.py` — then **say plainly
whether you are going to run the headless trial**, because it spends money and it is the only step
that produces evidence rather than inspection. If the user declines it, score the four lever axes
and mark `Prior` as unscored; do not guess it.

Write the report from `templates/audit-report.md`, lead with `Prior`, and if the connect axis
scored badly, fill `templates/instructions-block.md` and hand it over ready to paste.
