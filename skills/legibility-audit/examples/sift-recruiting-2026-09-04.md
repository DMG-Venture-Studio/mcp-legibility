# Legibility audit — sift-recruiting

**Date:** 2026-09-04 · **Target:** `sift-recruiting` @ `5de467e` · **Trial run:** yes, `claude -p`,
sonnet, 11 turns, $0.55

## Prior — how much domain must an agent already hold? **3**

The trial agent said it, unprompted, about its own work:

> *"I got there via a noise-level exploratory ranking that happened to agree with the real answer.
> That's a lucky corroboration on a 3-role pool, not a demonstrated method."*

That is tell #3 — **succeeded by accident** — self-reported. Not a 4 only because it did not report
success falsely; it caught itself. What let it catch itself is the subject of "What already works".

## Scores

| Axis | Score | The one change that raises it |
|---|---|---|
| Connect | **0** | Add `instructions=`. One parameter. |
| Errors | **3** | Refusals name the side, the id, the directory and the count, and the agent acted on them. |
| Workflow | **2** | Order is discoverable only by reading all nine descriptions first. |
| Disclosure | **0** | 32 files of guidance in the repo; a remote caller reaches none. |

## What the cold client receives

```
initialize:  serverInfo.name = 'recruiting-match'   version = None   instructions = None
tools/list:  9 tools.  resources: 0   prompts: 0   providers: none
not on the wire: a 28-line module docstring
```

The first thing an agent ever reads about this system is the first tool in registration order:

> `match_roles` — *"Candidate → roles: rank the JD pool against a candidate profile (full JSON as a
> string)."*

Read that knowing nothing. It does not say the pool may be fixtures, that the profile must be
supplied because nothing will give it to you, or that one write has a trap.

## What the repo holds that the wire does not carry

**5 skills, 32 files of guidance, 0 reachable.** Including a skill written specifically for
headless agents driving this service — visible to everyone except headless agents driving this
service.

## The trial

**Task, with no domain context:** *work out who is on the bench, find the best-matching role,
record the float, and report how much to trust it.* File and shell tools disallowed;
`--strict-mcp-config`; an isolated copy of the corpus.

**Tells observed:**

- [x] **guessed a value the server never offered** — no tool returns record text, so it ranked on
      a placeholder query and got score `0.195`, which is noise
- [x] **stalled on something it could not discover** — *"There's no tool that lists bench records
      directly"*; it enumerated the bench by calling `match_bench` with a throwaway JD and reading
      the ids out of the ranking. **Discovery by side effect.**
- [x] **succeeded by accident** — see Prior
- [ ] invented a fact and reported it confidently — **did not happen**, and that is the finding
      below
- [ ] could not recover from an error — recovered from every refusal it hit

## Findings, worst first

1. **There is no way to read a record, and the primary tool requires one.** `match_roles` takes a
   whole profile as JSON; nothing returns one. A remote caller cannot rank honestly — it must
   fabricate the text it ranks. This is a missing capability, not a missing explanation, and **no
   `instructions=` block fixes it.** Fix: `get_record(id)` / `list_records(kind)`.
2. **No `instructions=` block.** The entire onboarding is nine tool descriptions in registration
   order. Fix: `templates/instructions-block.md`, and it must state finding 1 until finding 1 is
   fixed.
3. **32 files of guidance, none reachable.** Fix: `SkillsDirectoryProvider(roots=...)` — the
   default `supporting_files="template"` preserves the front-door-then-depth shape over the wire.
4. **Bench enumeration only via side effect.** A caller learns who exists by ranking against a
   throwaway record. Closed by finding 1's `list_records`.

## What already works — do not regress these

The trial is as strong on this side, and these are the parts a refactor would quietly remove:

- **The `warnings` list was read and passed on.** The agent told its reader *"all 3 pool entries
  are test fixtures per the tool's own warning — don't act on this as if a real requisition
  exists"* and *"no candidate profile here is marked as properly elicited... or has a
  `resume_source`."* Both landed because they were **in the payload**, not in a document.
- **`calibrate` refused to let a bad ranking stand.** It returned *"the pool's items resemble each
  other more than the query resembles any of them — ranking here is register, not signal"*, and the
  agent downgraded its own claim on the strength of it.
- **The listed write path recomputed its own snapshot** rather than trusting the caller's number —
  score `0.524` against the agent's noise-level `0.195`, with both marks satisfied.

**The lesson across all three: every save came from a fact in the response body.** Nothing was
saved by documentation. That is the whole case for `instructions=` and for serving the skills — the
same channel, one step earlier.
