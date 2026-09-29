# Legibility audit — <target>

**Date:** <date>  ·  **Trial run:** <yes / no — a report without one is a lint, and says so>

## Prior — how much domain must an agent already hold?  **<0–4>**

<The one line from the trial transcript that proves it. Quote the agent, not yourself.>

Lower is better on this axis and it is the only one that matters; the four below are how you move
it.

## Scores

| Axis | Score | The one change that raises it |
|---|---|---|
| Connect | <0–4> | |
| Errors | <0–4> | |
| Workflow | <0–4> | |
| Disclosure | <0–4> | |

## What the cold client receives

<initialize payload; tools/list in registration order; resources; providers>

## What the repo holds that the wire does not carry

<N skills / M files of guidance, and how many reach a remote caller>

## The trial

**Task given, with no domain context:** <task>

**What it did:** <turns, tools called, what landed in the corpus>

**Tells observed:**

- [ ] guessed a value the server never offered
- [ ] stalled or asked for something it could not discover
- [ ] succeeded by accident — right call, wrong reason
- [ ] invented a fact and reported it confidently
- [ ] hit an error and could not recover

## Findings, worst first

1. **<finding>** — <what it costs a caller> — <the fix, paste-ready if possible>

## What already works — do not regress these

<The things the trial showed working. An audit that only lists faults gets the working parts
removed in the next refactor.>
