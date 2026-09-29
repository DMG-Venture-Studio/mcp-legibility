# Template: the `instructions=` block

Paste into `FastMCP(...)`. It rides the `initialize` response, so **every client gets it before it
calls anything** — no discovery step, no cooperation from the caller, no file it has to find.

Four parts, in this order. The second and third are the ones authors skip and callers need most.

```python
mcp = FastMCP(
    "<server-name>",
    version="<x.y.z>",
    instructions=(
        # 1. PURPOSE — one sentence. What this is for, in the caller's terms, not yours.
        "<What this server does, and for whom.>\n\n"

        # 2. ENTRY POINT — where to start. FastMCP's own example ends "Start with get_summary()".
        #    Without this a caller has a set of verbs and no order.
        "Start with <tool>() — <what it tells them and why it comes first>.\n\n"

        # 3. NON-GOALS — what it does NOT do. This is the highest-value sentence in the block,
        #    because it is what a caller will otherwise assume and report as fact.
        "This server does NOT <the thing a reasonable caller assumes it does>. "
        "<What it does instead, or where that lives.>\n\n"

        # 4. THE TRAP — the one call that succeeds while producing nothing usable, if there is one.
        "<tool>(<param>=...) <what it silently costs>.\n\n"

        # 5. DEPTH — where the rest is, and whether they can actually reach it.
        "<Served skills / a reference tool / 'nothing else crosses the wire'>."
    ),
)
```

## Worked, from a real audit

```python
instructions=(
    "Ranks a pool of job descriptions against candidate profiles, and records human judgments "
    "about pairs.\n\n"
    "Start with pool_stats() — it tells you how many records exist, and every ranking you get "
    "is 'closest of the N on file', never 'best in the market'.\n\n"
    "This server does NOT source roles. It has no crawler and no search. The pool is a directory "
    "someone filled; if it is empty, ranking refuses rather than returning nothing.\n\n"
    "You must supply record text yourself: match_roles takes a whole profile as JSON. There is no "
    "getter, so if you cannot read the record you cannot rank it honestly — say so rather than "
    "ranking on a placeholder.\n\n"
    "Every ranking carries a `warnings` list. Read it and pass it on: it is where 'these are "
    "fixtures, not live openings' and 'this profile has no résumé on file' are said."
)
```

## The test

Give the block to someone who has never seen the system and ask: *what would you call first, and
what would you be careful not to claim?* If they cannot answer both, the block is not done.
