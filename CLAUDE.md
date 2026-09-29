# mcp-legibility: agent instructions

This file is canonical. `AGENTS.md` and `.agents/README.md` point here.

## What this is

A tool that audits an MCP server and its repository for legibility on
connect: what a cold agent receives before it acts, and how much domain
knowledge it must already hold to succeed. It measures by running a real
headless agent against the target, not by inspecting. The score that matters
is `Prior`, and lower is better.

Read `skills/legibility-audit/SKILL.md` first. It is the audit, in order.

## Layout

| Path | What it is |
|---|---|
| `mcp/server.py` | FastMCP server exposing the static half as four tools: `connect_snapshot`, `repo_inventory`, `audit_repo`, `trial_command`. Serves the skill as resources. Never runs the trial. |
| `skills/legibility-audit/SKILL.md` | The procedure. The plugin's front door. |
| `skills/legibility-audit/scripts/probe_connect.py` | Static: what a client receives on connect, read from the server source with `ast`. |
| `skills/legibility-audit/scripts/inventory_repo.py` | Static: skills, supporting files, ordering claims, reachability. |
| `skills/legibility-audit/scripts/headless_trial.py` | Spawns `claude -p` isolated to the target MCP. Spends money. |
| `skills/legibility-audit/references/rubric.md` | The five axes and their levels. Scoring is judgement against described levels, not arithmetic. |
| `skills/legibility-audit/references/fastmcp-legibility.md` | FastMCP's mechanisms and what each buys a cold caller. |
| `skills/legibility-audit/templates/` | The report and the instructions block. |
| `skills/legibility-audit/examples/` | Two real audits. Keep them; they are the evidence the method works. |
| `docs/` | The GitHub Pages site. Plain HTML and CSS. |
| `tests/` | Unit tests over the static scripts and the server self-test. |

## Commands

    python3 -m unittest discover -s tests -v                              # tests
    uv run --script skills/legibility-audit/scripts/probe_connect.py --repo .    # static, free
    uv run --script skills/legibility-audit/scripts/inventory_repo.py --repo .   # static, free
    uv run --script mcp/server.py --selftest                              # the server audits this repo
    uv run --script skills/legibility-audit/scripts/headless_trial.py --repo <path> --task "..."   # spends money

## Rules

- Each script is a single file with inline `uv` script metadata and no
  dependencies beyond the standard library; the server alone depends on
  `fastmcp`. Keep it that way.
- Never make the headless trial run implicitly. It spends real money and
  takes minutes. `trial_command` returns the line; a person runs it.
- Scoring stays a judgement against the rubric's described levels. Do not add
  a script that averages the five axes into a number.
- Every function has a docstring. Refusals are returned as values, never as
  tracebacks; see `Refused` in the server.
- The two static scripts must agree with each other. `audit_repo` reconciles
  the inventory's conditional reachability finding against what the server
  declares; keep that reconciliation when either script changes.
- No personal names anywhere: code, comments, docs, examples, commits. Commits
  use the studio identity `DMG <dmg@noreply.invalid>`. No emojis. No pricing
  language beyond the plain statement that a trial spends money.
- The examples in `skills/legibility-audit/examples/` are real runs from a
  dated day. Do not edit their numbers. Add a new dated file for a new run.

## Where to change what

- A new finding on the connect axis: `findings()` in `probe_connect.py`, and
  the matching row in `references/rubric.md`.
- A new finding on workflow or disclosure: `findings()` in
  `inventory_repo.py`, same rule.
- A new tell in the trial: `tells()` in `headless_trial.py` is heuristic hints
  only; the list of tells a reader looks for is in `SKILL.md` and the report
  template. Change all three together.
- The docs site is hand-written HTML in `docs/index.html`; the example report
  there is rendered from the examples directory by hand. When an example
  changes, change the page.
