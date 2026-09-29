# mcp-legibility

**Can an agent that knows nothing about your system use it correctly on the
first try?**

That is the only question this tool answers, and it answers it by running the
experiment rather than by reading your code. It puts a real headless agent in
front of your MCP server with no domain context at all, gives it a task, and
records what the agent does: where it guessed, where it stalled, where it got
the right answer for the wrong reason, and where it reported success on
something that was wrong.

Docs and an example report: https://dmg-venture-studio.github.io/mcp-legibility/

## Why it exists

An MCP server ships with documentation. Almost none of it reaches the agents
that connect to it. Skills, READMEs, and contracts live in a repository; a
remote client sees the protocol and nothing else. So the better the docs, the
more confident the author, and the worse the surprise when a headless agent
misuses a tool that "was clearly documented".

The author cannot see this failure, because the author cannot un-know the
domain. The docstring reads fine to them. A linter cannot see it either: a
linter can tell you a tool has a docstring, not that the docstring's first line
is the entire onboarding a remote caller will ever get.

So this tool does not grade prose. It measures one number, which it calls
**Prior**: how much the agent had to already know to succeed. The optimum is
zero.

## What it measures

Five axes, scored 0 to 4. Four are levers; the fifth is the outcome.

| Axis | The question | Optimum |
|---|---|---|
| Connect | What does a cold client receive before it acts? | An instructions block with an entry point |
| Errors | Do failures teach the next call, or drop the stream? | Typed, actionable, self-correcting |
| Workflow | Can the steps be run out of order? | Order is enforced, not merely documented |
| Disclosure | Is there a thin front door that points deeper? | Progressive: not a wall, not a void |
| **Prior** | **How much must the agent already know?** | **Zero** |

`Prior` runs the other way: lower is better, and a 4 means the agent completed
the task wrongly while reporting success, which is the worst outcome in the
rubric because nothing downstream knows it happened. The full rubric with what
each level means is in `skills/legibility-audit/references/rubric.md`.

## How a run works

Three steps. The first two are static and free. The third is the one that
produces evidence.

1. **Connect snapshot.** Reads the server source and reports exactly what a
   client receives on `initialize` and `tools/list`: the instructions block or
   its absence, the tools in registration order, resources, providers. Needs
   no credentials, no running server, no network.

       uv run --script skills/legibility-audit/scripts/probe_connect.py --repo <path>

2. **Repo inventory.** Lists the skills and guidance the repository holds, the
   workflow order they claim in prose, and how much of it a remote caller can
   actually reach. Usually the answer is none.

       uv run --script skills/legibility-audit/scripts/inventory_repo.py --repo <path>

3. **Headless trial.** Spawns `claude -p` with only the target server
   attached, file and shell tools disallowed, and `--strict-mcp-config`, so
   the agent cannot read the repository. That isolation is the experiment: a
   remote caller cannot read your skills either. The trial runs against a
   copy of any state in a temp directory, so it never touches a live corpus.

       uv run --script skills/legibility-audit/scripts/headless_trial.py --repo <path> --task "<what to do>"

   This step spends money, because a real agent runs. Budget a few tens of
   cents per trial. Nothing in this tool runs it silently.

## What a run produces

- A scored report from `templates/audit-report.md`: `Prior` first with the
  transcript line that proves it, then the four levers, each with the one
  change that would raise it.
- A paste-ready `instructions=` block from `templates/instructions-block.md`
  when the connect axis scores badly, which is the most common finding and the
  cheapest fix.
- The trial transcript, read for five tells: guessed a value the server never
  offered; stalled on something it could not discover; succeeded by accident;
  invented a fact and reported it confidently; hit an error and could not
  recover.

Two real reports are in `skills/legibility-audit/examples/`. The A/B in there
put the same agent in front of two servers on the same day. The illegible one
took 11 turns and scored Prior 3; the legible one took 5 turns and scored
Prior 0. Same model, same harness, same task shape. The only variable was what
crossed the wire.

## Install

As a Claude Code plugin, which gives you the `/legibility-audit` skill and an
MCP server that exposes the static half as tools:

    /plugin marketplace add DMG-Venture-Studio/mcp-legibility
    /plugin install mcp-legibility

Or clone it and run the scripts directly. Each script declares its own
dependencies inline, so `uv run --script` is the whole setup. The scripts need
Python 3.11 or later; the server needs `fastmcp` 3, which `uv` fetches on
first run.

Use inside Claude Code:

    /legibility-audit                      # audit the repo you are in
    /legibility-audit --target <path>      # audit another repo
    /legibility-audit --no-headless        # static only, spends nothing

A report without the trial is a lint, and the tool says so in the report.

## The server audits itself

`mcp/server.py` is an MCP server that wraps the static scripts as tools, so an
agent can run the audit over the wire. It holds itself to the same standard:
it ships an `instructions=` block with an entry point and a stated non-goal,
and serves its own skill as resources through `SkillsDirectoryProvider`, so a
remote caller can read the rubric it is being scored against. It deliberately
does not run the headless trial as a tool; `trial_command` returns the exact
line for a person to run, so the spend is always a human keystroke.

    uv run --script mcp/server.py --selftest

## Tests

    python3 -m unittest discover -s tests -v

The tests run the two static scripts against this repository and check the
findings, and run the server's self-test if `uv` is available.

## Layout

    mcp/server.py                              the MCP server: four tools over the scripts
    skills/legibility-audit/SKILL.md           the audit, in order, for an agent or a person
    skills/legibility-audit/scripts/           probe_connect, inventory_repo, headless_trial
    skills/legibility-audit/references/        the rubric; FastMCP's legibility mechanisms
    skills/legibility-audit/templates/         the report; the instructions block
    skills/legibility-audit/examples/          two real audits from 2026-09-04
    docs/                                      the published site
    tests/                                     unit tests over the static scripts
    .claude-plugin/                            plugin and marketplace manifests

## License

License to be decided by the studio.
