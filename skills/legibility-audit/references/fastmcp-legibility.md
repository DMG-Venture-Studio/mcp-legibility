# What FastMCP gives you, and what each mechanism buys a cold caller

Sourced from gofastmcp.com (`/servers/server#configuration-reference`, `/servers/providers/skills`,
`/servers/middleware`), read 2026-09-04. Version badges are FastMCP's own.

The ordering is by cost-to-benefit for legibility, not by importance to the library.

## 1. `instructions=` — one parameter, the largest single win

    mcp = FastMCP(
        "DataAnalysis",
        instructions="Provides tools for analyzing numerical datasets. Start with get_summary() for an overview.",
    )

FastMCP describes it as a "purpose description surfaced to LLMs understanding server
functionality... Helps clients understand interaction patterns." It rides the `initialize`
response, so **every client gets it before it calls anything**, with no discovery step and no
cooperation from the caller.

Note the shape of FastMCP's own example: a sentence of purpose, then **an entry point** — *"Start
with `get_summary()`."* That second clause is doing most of the work. A server without it hands the
agent a set of verbs and no order.

Related identity fields, all constructor arguments: `name`, `version`, `website_url` (2.13+),
`icons` (2.13+).

**Audit rule:** absent `instructions` is a finding on every server, always. It is the cheapest fix
in this document and the only one that needs no client cooperation.

## 2. Skills as resources — `SkillsDirectoryProvider` (3.0.0+)

    from fastmcp.server.providers.skills import SkillsDirectoryProvider
    # import path verified against fastmcp 3.4.7, 2026-09-04; the module also ships
    # ClaudeSkillsProvider / CursorSkillsProvider / CodexSkillsProvider and friends

    mcp = FastMCP("MyServer", providers=[SkillsDirectoryProvider(roots=Path("./skills"))])

Exposes every skill over the protocol under the `skill://` scheme:

- `skill://<name>/SKILL.md` — the main instruction file
- `skill://<name>/_manifest` — a synthetic JSON resource listing every file with size and SHA-256
- `skill://<name>/<supporting file>` — references, examples, assets

```json
{"skill": "pdf-processing", "files": [{"path": "SKILL.md", "size": 1234, "hash": "sha256:abc123..."}]}
```

Constructor: `roots`, `supporting_files` (`"template"` or `"resources"`), `reload`.

**`supporting_files="template"` is progressive disclosure, implemented for you.** FastMCP's own
words: clients see only the main file and the manifest in `list_resources()`, then discover
supporting files by reading the manifest. That is exactly the front-door-then-depth shape a good
skill already has — the default mode preserves it over the wire instead of flattening it.

Client side, in `fastmcp.utilities.skills`: `list_skills(client)`, `get_skill_manifest(client, name)`,
`download_skill(client, name, destination)`, `sync_skills(client, destination)` — all taking
`overwrite` (default `False`).

**This is the answer to the reachability trap.** A repository whose real instructions live in
`skills/` has two options: copy the essentials into `instructions=`, or serve the skills. The
manifest's hashes are the same discipline a repo-side skills lock already holds, so the two can be
checked against each other.

**Audit rule:** a repo with skills, a served MCP, and no provider is documentation its own audience
cannot read.

## 3. Typed errors — the difference between a hint and a dead end

Raise the operation's own error type and it reaches the client as a message rather than a
transport failure:

| Operation | Error type |
|---|---|
| Tool calls | `ToolError` |
| Resource reads | `ResourceError` |
| Prompt retrieval | `PromptError` |
| General requests | `McpError` |

    from fastmcp.exceptions import ToolError
    raise ToolError("Access denied")

And the built-in, which converts what you did not anticipate:

    from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
    mcp.add_middleware(ErrorHandlingMiddleware(include_traceback=True, transform_errors=True))

Also `RetryMiddleware` (exponential backoff) for the transient class.

**Why this is a legibility mechanism and not an ops one.** An agent can reason about *"candidate
'x' names no record in <dir> (3 on file)"*. It cannot reason about a dropped stream — there is no
sentence in it. An unhandled exception that surfaces as a transport error costs the agent its whole
run, and the fix is one middleware.

**Audit rule:** any path from a tool body to an unhandled exception is a legibility defect, not
just a robustness one.

## 4. Middleware — where per-call legibility gets stamped

    from fastmcp.server.middleware import Middleware, MiddlewareContext

    class M(Middleware):
        async def on_call_tool(self, context, call_next):
            result = await call_next(context)
            return result

    mcp.add_middleware(M())   # registration order = execution order

Hooks: `on_message`, `on_request`, `on_notification`, `on_call_tool`, `on_read_resource`,
`on_get_prompt`, `on_list_tools`, `on_list_resources`, `on_list_prompts`, `on_initialize`
(returns `InitializeResult`), `on_discover`. Override only what you need.

`MiddlewareContext` carries `method`, `source`, `type`, `message`, `timestamp`, `fastmcp_context`.
Per-request state:

    context.fastmcp_context.set_state("user_id", user_id)   # middleware
    user_id = ctx.get_state("user_id")                      # tool

Built-ins worth knowing for an audit: `LoggingMiddleware` / `StructuredLoggingMiddleware`
(`include_payloads`, `max_payload_length`), `TimingMiddleware` / `DetailedTimingMiddleware`,
`ResponseCachingMiddleware`, `RateLimitingMiddleware`, `ResponseLimitingMiddleware`,
`PingMiddleware` (3.0+).

Two legibility uses specifically:

- **`on_list_tools`** can annotate or filter what a caller sees, so the surface presented can depend
  on state — e.g. naming that the corpus is empty at the moment the tools are listed.
- **`on_initialize`** returns the `InitializeResult`, which is where a dynamic instructions block
  would go if a static one is not enough.

## 5. Behaviour flags that change what a caller can figure out

- `mask_error_details` — obscures implementation detail in errors. Security win, **legibility
  cost**; audit whether the masked message still names a next action.
- `strict_input_validation` (2.13+, default `False`) — off means compatible types are coerced. A
  caller passing the wrong shape may succeed and never learn it was wrong.
- `on_duplicate` (default `"warn"`) — a silently replaced tool is a surface that changed without
  saying so.
- `dereference_schemas` (default `True`) — flattens `$ref`, which makes `inputSchema` readable to
  a client that does not resolve references.
- `list_page_size` (3.0+) — paginated listings; a caller that stops at page one sees a partial
  surface.

## The short version

| Want | Mechanism | Cost |
|---|---|---|
| An agent oriented before its first call | `instructions=` with an entry point | one parameter |
| Your skills readable by remote agents | `SkillsDirectoryProvider` | one provider |
| Progressive disclosure over the wire | `supporting_files="template"` (default) | zero, it is the default |
| Errors an agent can act on | `ToolError` + `ErrorHandlingMiddleware` | one middleware |
| Provenance on every call | `on_call_tool` + `set_state` | one middleware |
