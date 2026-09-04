# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""What a cold MCP client receives on connect — read from the server's source, not from a socket.

Static on purpose. A live probe needs credentials, a running server and a reachable host; this
needs a file. It answers the question that matters at audit time — *what is in the `initialize`
payload and `tools/list`* — for a server nobody has deployed yet, and for one whose token you do
not hold.

The one thing it cannot see is a surface built at runtime (tools registered in a loop, a dynamic
provider). It says so rather than reporting a smaller surface as the whole one.

    probe_connect.py --repo <path>            # finds the server under <path>
    probe_connect.py --server <file.py>       # a specific server file
    probe_connect.py --repo <path> --json
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

TOOL_DECORATORS = ("tool",)
RESOURCE_DECORATORS = ("resource",)
PROMPT_DECORATORS = ("prompt",)


@dataclass
class Surface:
    """Everything a client can learn before it calls anything, plus what it cannot."""

    server_file: str
    name: str | None = None
    instructions: str | None = None
    version: str | None = None
    tools: list[dict] = field(default_factory=list)
    resources: list[dict] = field(default_factory=list)
    prompts: list[dict] = field(default_factory=list)
    middleware: list[str] = field(default_factory=list)
    providers: list[str] = field(default_factory=list)
    module_docstring_lines: int = 0
    dynamic_registration: list[str] = field(default_factory=list)


def _decorator_kind(node: ast.AST) -> str | None:
    """Which registration decorator this is, if any — `@mcp.tool`, `@mcp.tool()`, or neither."""
    target = node.func if isinstance(node, ast.Call) else node
    attr = getattr(target, "attr", None)
    if attr in TOOL_DECORATORS:
        return "tool"
    if attr in RESOURCE_DECORATORS:
        return "resource"
    if attr in PROMPT_DECORATORS:
        return "prompt"
    return None


def _string_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level `NAME = "..."` assignments, so a constant can be resolved by name.

    A long `instructions=` block is almost always hoisted to a constant rather than written inline
    at the call. Reading only `ast.Constant` reported those servers as having NO instructions —
    a false negative, and the worst kind: it tells an author their fix did not land.
    """
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        out[t.id] = node.value.value
        # implicit concatenation across lines parses as a JoinedStr/BinOp-free Constant only when
        # every part is literal; ast.unparse round-trips the rest well enough to detect presence
        elif isinstance(node, ast.Assign) and isinstance(node.value, (ast.JoinedStr, ast.BinOp)):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = ast.unparse(node.value)
    return out


def _literal(node: ast.AST, consts: dict[str, str] | None = None) -> str | None:
    """An argument's string value — written inline, or resolved from a module-level constant."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and consts:
        return consts.get(node.id)
    # a parenthesised run of adjacent string literals folds to one Constant; anything else that
    # is still a string expression (implicit concat with f-strings) is reported as present
    if isinstance(node, ast.JoinedStr):
        return ast.unparse(node)
    return None


def _params(fn: ast.FunctionDef) -> list[str]:
    """The tool's parameter names, in order — what shows up in `inputSchema`."""
    return [a.arg for a in fn.args.args if a.arg not in ("self", "ctx", "context")]


def read_surface(path: Path) -> Surface:
    """Parse one server file into the surface a client would see."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    consts = _string_constants(tree)
    surface = Surface(server_file=str(path))
    doc = ast.get_docstring(tree)
    surface.module_docstring_lines = len(doc.splitlines()) if doc else 0

    for node in ast.walk(tree):
        # the constructor: FastMCP(...)
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "FastMCP":
            if node.args:
                surface.name = _literal(node.args[0], consts)
            for kw in node.keywords:
                if kw.arg in ("name", "instructions", "version"):
                    setattr(surface, kw.arg, _literal(kw.value, consts))
                if kw.arg == "providers":
                    surface.providers += [ast.unparse(e) for e in getattr(kw.value, "elts", [])]
                if kw.arg == "middleware":
                    surface.middleware += [ast.unparse(e) for e in getattr(kw.value, "elts", [])]
        # .add_middleware(...)
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "add_middleware":
            surface.middleware += [ast.unparse(a) for a in node.args]
        # registration inside a loop or comprehension is a surface this cannot enumerate
        if isinstance(node, (ast.For, ast.While)):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call) and _decorator_kind(inner):
                    surface.dynamic_registration.append(ast.unparse(inner)[:80])

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            kind = _decorator_kind(dec)
            if kind is None:
                continue
            doc = ast.get_docstring(node) or ""
            entry = {
                "name": node.name,
                "first_line": doc.split("\n")[0] if doc else "",
                "description_chars": len(doc),
                "params": _params(node),
                "has_description": bool(doc),
            }
            getattr(surface, kind + "s").append(entry)
    return surface


def find_server(repo: Path) -> Path | None:
    """The most likely MCP server file under `repo` — a file that constructs a FastMCP."""
    candidates = sorted(
        p for p in repo.rglob("*.py")
        if ".venv" not in p.parts and "node_modules" not in p.parts
        and "FastMCP(" in p.read_text(encoding="utf-8", errors="ignore")
    )
    return candidates[0] if candidates else None


def findings(s: Surface) -> list[str]:
    """The connect-axis findings, worst first — see references/rubric.md axis A."""
    out = []
    if not s.instructions:
        out.append(
            "NO `instructions=` BLOCK. The initialize response carries a server name and nothing "
            "else, so a cold client's entire onboarding is the tool descriptions below. This is "
            "the cheapest fix available: one constructor parameter, no client cooperation needed."
        )
    elif not any(w in s.instructions.lower() for w in ("start with", "begin", "first", "call ")):
        out.append(
            "`instructions=` exists but names no ENTRY POINT. FastMCP's own example ends "
            "'...Start with get_summary() for an overview.' Without that clause a caller gets "
            "purpose and no order."
        )
    skills_provider = any("Skills" in p for p in s.providers)
    if not s.resources and not s.providers:
        out.append(
            "NO RESOURCES AND NO PROVIDERS. Nothing but tools crosses the wire, so any skill, "
            "contract or reference in this repo is unreachable by a remote caller. See "
            "SkillsDirectoryProvider."
        )
    elif skills_provider:
        out.append(
            "OK: a skills provider is declared, so this repo's skills ARE reachable over the wire "
            "(skill://<name>/SKILL.md plus a _manifest). Resources are supplied at request time, "
            "which is why the static count above is 0 — that is not a finding."
        )
    elif not s.resources:
        out.append(
            f"PROVIDERS DECLARED BUT NO SKILLS PROVIDER ({', '.join(s.providers)}); check whether "
            "this repo's written guidance reaches a remote caller by any route."
        )
    if s.module_docstring_lines >= 10 and not s.instructions:
        out.append(
            f"THE BEST EXPLANATION IS UNREACHABLE: a {s.module_docstring_lines}-line module "
            "docstring that never crosses the wire, and no instructions block that does."
        )
    undescribed = [t["name"] for t in s.tools if not t["has_description"]]
    if undescribed:
        out.append(f"TOOLS WITH NO DESCRIPTION: {', '.join(undescribed)}")
    if s.tools:
        out.append(
            f"FIRST TOOL IN REGISTRATION ORDER is `{s.tools[0]['name']}` — its first line is the "
            f"first thing an agent reads about this system: \"{s.tools[0]['first_line']}\""
        )
    if s.dynamic_registration:
        out.append(
            "DYNAMIC REGISTRATION detected; the surface above may be incomplete. "
            + "; ".join(s.dynamic_registration[:3])
        )
    return out


def main() -> int:
    """Print the cold-connect surface and the connect-axis findings."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, help="repository to search for a server")
    ap.add_argument("--server", type=Path, help="a specific server file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = args.server or (find_server(args.repo) if args.repo else None)
    if path is None or not path.exists():
        print("refused: no file constructing a FastMCP server was found", file=sys.stderr)
        return 2
    surface = read_surface(path)
    if args.json:
        print(json.dumps({"surface": asdict(surface), "findings": findings(surface)}, indent=2))
        return 0

    print(f"=== what a cold client receives from {surface.server_file} ===\n")
    print("initialize:")
    print(f"  serverInfo.name : {surface.name!r}")
    print(f"  version         : {surface.version!r}")
    print(f"  instructions    : {surface.instructions!r}")
    print(f"\ntools/list ({len(surface.tools)}, in registration order):")
    for t in surface.tools:
        print(f"  {t['name']:28} {t['first_line'][:88]}")
    print(f"\nresources: {len(surface.resources)}   prompts: {len(surface.prompts)}")
    print(f"fastmcp middleware: {surface.middleware or 'none'}  (ASGI middleware passed to run() is separate and not counted here)")
    print(f"providers:  {surface.providers or 'none'}")
    print(f"\nnot on the wire: module docstring, {surface.module_docstring_lines} lines")
    print("\n=== findings (connect axis) ===")
    for i, f in enumerate(findings(surface), 1):
        print(f"  {i}. {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
