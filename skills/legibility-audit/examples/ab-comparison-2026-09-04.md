# The A/B — same harness, same model, two servers

Both trials on 2026-09-04, `claude -p`, sonnet, `--strict-mcp-config`, file and shell tools
disallowed. The only variable is the surface.

| | sift-recruiting | mcp-legibility |
|---|---|---|
| **Prior** | **3** | **0** ← optimum |
| Turns | 11 | 5 |
| Cost | $0.55 | $0.15 |
| `instructions=` | absent | present, with an entry point |
| Skills over the wire | 0 of 32 files | all, via `SkillsDirectoryProvider` |
| Outcome | right answer, wrong method, self-caught | right answer, calibrated confidence |

**A legible surface was 3.7× cheaper and less than half the turns.** Legibility is not only a
correctness property; the agent spent six extra turns on the illegible one working out what it was
looking at.

## sift-recruiting — Prior 3

The agent had to enumerate the bench through a side channel and rank on a placeholder, because no
tool returns a record:

> *"There's no tool that lists bench records directly, so I discovered the sole candidate by
> probing `match_bench` with a throwaway JD and reading the returned candidate id."*

> *"I got there via a noise-level exploratory ranking that happened to agree with the real answer.
> That's a lucky corroboration on a 3-role pool, not a demonstrated method."*

Tell #3, **succeeded by accident**, self-reported. It avoided a 4 only because payload warnings and
`calibrate` gave it enough to catch itself.

## mcp-legibility — Prior 0

Called the entry point the instructions named, answered correctly, and — the part that matters —
**separated inspected fact from its own judgement without being asked**:

> *"The structural facts... are directly inspected, not inferred — high confidence. Which finding
> is 'most important' is my synthesis on top of the raw list — a reasonable read, but a judgment
> call."*

Then it surfaced the caveat that makes the whole method honest, quoting a source it could only have
got over the wire:

> *"I did not run the headless trial, so I have no evidence of what an agent actually does when it
> hits this gap. **The server's own instructions are explicit that a report without a trial is a
> lint, not evidence.**"*

That sentence is in the `instructions=` block. It crossed the wire, the agent read it, and it
changed what the agent claimed. It then found `trial_command` unprompted and offered the generated
command.

Five tells, all clear: no guessed value, no stall, no accident, no invented fact, no unrecovered
error.

## What this proves about the mechanism, not the tool

Every save in **both** trials came from something **in the response body** — instructions, a
`warnings` list, a `calibrate` verdict. Nothing was saved by documentation sitting in a repository.
The difference between Prior 3 and Prior 0 is entirely how much of what the author knew was placed
where a cold caller would meet it.

## An honest note on the harness

The tells heuristic fired `SAW 'unlisted'` on the mcp-legibility run. False positive: the agent was
*describing* sift-recruiting's contract, not reaching for the flag. The heuristics are substring
hints over the transcript and fire on discussion as well as use — which is why `tells()` is
documented as hints and the skill says to read the transcript. Left as-is rather than tuned, since
a hint that occasionally over-fires is safer than one tuned until it under-fires.
