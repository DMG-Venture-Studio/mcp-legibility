# mcp-legibility

**Can an agent that knows nothing about your system use it correctly on the first try?**

That is the only question this plugin answers, and it answers it empirically rather than by
inspection: it spawns a real headless agent (`claude -p`) against your MCP server with **no domain
context at all**, gives it a task, and watches what happens.

Static linting tells you a tool has a docstring. It cannot tell you that the docstring's first
line is the entire onboarding a remote agent will ever receive, that the pool it ranks against is
three fixtures, or that one boolean parameter silently makes the write unreadable. Those are
legibility failures, they are invisible to the author, and they are the ones that burn a run.

## The five axes

| Axis | The question | Optimum |
|---|---|---|
| **Connect** | What does a cold client receive before it acts? | Instructions block + an entry point |
| **Errors** | Do failures teach the next call, or drop the stream? | Typed, actionable, self-correcting |
| **Workflow** | Can the steps be run out of order? | Order is enforced, not merely documented |
| **Disclosure** | Is there a thin front door that points deeper? | Progressive, not a wall and not a void |
| **Prior** | How much must the agent already know? | **Zero** |

`Prior` is the score that matters. The others are how you move it.

## Use

    /legibility-audit                      # audit the repo you are in
    /legibility-audit --target <path>      # audit another repo
    /legibility-audit --no-headless        # static only, spends nothing

The headless trial spends tokens: it runs a real agent. It is also the only part that produces
evidence rather than opinion, so skipping it downgrades the report to a lint.

## What it produces

A scored report, a filled `templates/instructions-block.md` you can paste into your server, and a
transcript of the headless trial with every place the agent guessed, stalled, or invented a fact.

Built against FastMCP's own documentation — see `skills/legibility-audit/references/fastmcp-legibility.md`,
which carries the mechanisms (`instructions=`, `SkillsDirectoryProvider`, middleware hooks, typed
errors) and what each one buys a cold caller.
