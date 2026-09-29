# The rubric — five axes, scored 0 to 4

Score what the surface **does**, never what the repository *contains*. A perfect SKILL.md that no
remote caller can read scores zero on every axis it was supposed to help.

`Prior` is the outcome. The other four are the levers. Report all five; lead with `Prior`.

---

## A. Connect — what a cold client receives before it acts

| Score | State |
|---|---|
| 0 | Server name only. No `instructions`, no resources, no prompts. Tool descriptions are the entire onboarding. |
| 1 | Tool descriptions are individually good, but nothing orients across them and nothing says where to start. |
| 2 | An `instructions` block exists and describes purpose. No entry point, no stated non-goals. |
| 3 | Instructions name purpose, an entry point, and at least one thing the server does **not** do. |
| 4 | The above, plus skills or reference material served as resources, so depth is reachable over the wire. |

**Evidence:** the `initialize` payload and `tools/list`, from `probe_connect.py`. Not the README.

## B. Errors — do failures teach the next call?

| Score | State |
|---|---|
| 0 | Failures surface as transport errors or dropped streams. Nothing for an agent to reason about. |
| 1 | Errors are typed but describe symptoms — "invalid argument", "not found". |
| 2 | Errors name what was wrong and where. |
| 3 | Errors name the wrong thing **and the next action**, with enough state to act ("3 on file"). |
| 4 | The above, and following the named action succeeds — verified in the trial, not assumed. |

**Evidence:** deliberately induce three failures — a bad id, a missing required input, a wrong-order
call — and read what comes back. Score the worst of the three.

## C. Workflow — can steps be run out of order?

| Score | State |
|---|---|
| 0 | Order matters and nothing enforces it; a wrong-order call succeeds and produces something wrong. |
| 1 | Order is documented in prose the caller has no way to reach. |
| 2 | Order is discoverable from tool descriptions if the caller reads all of them first. |
| 3 | Wrong order refuses, naming the missing prerequisite. |
| 4 | Wrong order refuses **and** the refusal is a runnable next step. |

**The distinction that matters:** a workflow enforced only in prose is not enforced. Test it by
calling the last step first.

## D. Disclosure — is there a front door that points deeper?

| Score | State |
|---|---|
| 0 | Nothing, or everything at once: a wall of text a caller must consume before acting. |
| 1 | One flat layer. Everything the server says, it says immediately. |
| 2 | Layers exist in the repo but are flattened or unreachable over the wire. |
| 3 | A thin front door names the depth and how to get it. |
| 4 | Depth is served and self-describing — e.g. a manifest a client reads to decide what else to fetch. |

**Anti-pattern both ends.** A void makes the agent guess; a wall makes it skim. FastMCP's
`supporting_files="template"` is the shape: main file plus manifest first, everything else on
demand.

## E. Prior — how much domain must the agent already hold? **(the score that matters)**

| Score | State |
|---|---|
| 0 | **Optimum.** A competent agent with no context completes the task correctly, or refuses for a reason the surface gave it. |
| 1 | Completes it after one recoverable wrong turn the surface corrected. |
| 2 | Completes it only by reading material outside the protocol. |
| 3 | Completes it only with domain knowledge no artefact supplies — the agent guessed and happened to be right. |
| 4 | Cannot complete it, or completes it **wrongly while reporting success**. |

Note the direction: on this axis **lower is better**, and it is inverted from the other four on
purpose. `Prior 4` is the worst outcome in the whole rubric, worse than an outright failure,
because nothing downstream knows it happened.

**Evidence:** the headless trial transcript. This axis cannot be scored by inspection — the author
of a system cannot un-know it, which is the entire reason the trial exists.

---

## Reporting

Lead with `Prior` and the transcript line that proves it. Then the four levers, each with the one
change that would raise it. A finding with a paste-ready fix gets acted on; a finding without one
gets filed.

**Score the surface a stranger meets, not the one you know is there.** If a fact only exists in a
file that does not cross the wire, it does not count toward any score above.
