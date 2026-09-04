---
name: legibility-audit
description: Audit an MCP server and its repository for legibility on connect — what a cold agent receives before it acts, whether errors teach, whether workflows can be run out of order, how much progressive disclosure exists, and how much domain knowledge an agent must already hold to execute correctly. Use when asked to audit an MCP server, check agent-experience or "legibility", find out why a headless agent misused a tool, or before publishing an MCP surface others will connect to. Runs a real headless agent against the target rather than inspecting it.
---

# Legibility on connect

**The question: can an agent that knows nothing about this system use it correctly on the first
try?** Everything below serves that one question, and the score that matters is `Prior` — how much
the agent had to already know. Optimum is zero.

## Why inspection is not enough

An author cannot see their own system's legibility, because they cannot un-know the domain. The
docstring reads fine *to them*. So this audit does not grade prose; it puts a real agent with no
context in front of the server and records what it does. Step 3 is the evidence. Steps 1–2 only
tell you where to look.

## The audit, in order

### 1. Connect snapshot — what a cold client actually receives

    uv run --script scripts/probe_connect.py --repo <path>

Static, free, needs no credentials or running server: it reads the server source and reports the
`initialize` payload and `tools/list` a client would get. Look for, in this order:

- **An `instructions=` block.** Its absence is the single most common finding, and the most
  expensive: it is the only field in the protocol whose whole job is orienting a caller.
- **An entry point.** Even with instructions, does anything say *start here*? FastMCP's own example
  is shaped `"...Start with get_summary() for an overview."`
- **Resources and prompts.** Usually zero. A server with tools only has one channel and it is a
  list of verbs.
- **The first tool in registration order.** `tools/list` is ordered, and the first description is
  what an agent reads first about your system. Read it as though you know nothing.

**A module docstring is not an instruction set.** It never crosses the wire. Check whether the
best explanation of the system is in a file no remote caller will ever open.

### 2. Repo inventory — the workflows, and whether anything enforces them

    uv run --script scripts/inventory_repo.py --repo <path>

Skills, their references, and the graph of what points at what. Then the question that matters:
**for every ordering rule stated in prose, what happens if a caller does it in the wrong order?**
Prose is not enforcement. A workflow that only exists in a SKILL.md is a workflow a headless caller
will not follow, because it never read the SKILL.md (see §"The reachability trap").

### 3. The headless trial — the only step that produces evidence

    uv run --script scripts/headless_trial.py --repo <path> --task <task-file>

Spawns `claude -p` with **only** the target MCP attached and no domain context, hands it a task,
and records the transcript. Then read it for the five tells:

| Tell | What it means |
|---|---|
| **Guessed a value** the server never offered | a vocabulary that exists only in the author's head |
| **Stalled or asked** for something it could not discover | a required input with no discovery path |
| **Succeeded by accident** — right call, wrong reason | the surface rewarded a wrong model of itself |
| **Invented a fact** and reported it confidently | the payload did not carry a caveat it needed |
| **Hit an error and could not recover** | the error named a symptom, not a next action |

The last one is the sharpest. An error an agent can act on is worth more than three paragraphs of
documentation it will never load.

### 4. Score and report

**Say plainly whether you ran the trial.** It spends money, so the user may decline it — and if they
do, score the four lever axes and mark `Prior` **unscored**. Do not estimate it: an inspected guess
at the one axis that requires evidence is the failure this whole plugin exists to name.

`references/rubric.md` holds the five axes and what each level means. **Scoring is a judgement
against described levels, not arithmetic** — there is deliberately no score.py, because a script
that averaged five judgement calls into a number would manufacture precision the evidence does not
have. Write the report from
`templates/audit-report.md`, and if the connect axis scored badly, fill
`templates/instructions-block.md` and hand it over — a finding with a paste-ready fix is acted on;
one without is filed.

## The reachability trap

The failure this plugin exists to catch, stated once:

**Documentation written for headless agents is usually unreachable by headless agents.** Skills,
READMEs and contracts live in a repository. A remote MCP client sees the protocol and nothing else
— no files, no repo, no plugin. So the better the docs, the more confident the author, and the
worse the surprise.

Always ask of any explanatory artefact: **does this cross the wire?** If it does not, either move
what matters into `instructions=` and the tool descriptions, or serve the skills as resources
(`SkillsDirectoryProvider` — `references/fastmcp-legibility.md`). Both are cheap. Neither is
automatic.

## Read next

- `references/fastmcp-legibility.md` — the mechanisms FastMCP gives you and what each buys a cold
  caller, from FastMCP's own docs.
- `references/rubric.md` — the five axes, their levels, and how to score honestly.
- `templates/instructions-block.md` — the paste-ready fix for the most common finding.
