# /// script
# requires-python = ">=3.11"
# dependencies = ["fastmcp>=3,<4"]
# ///
"""The legibility audit as MCP tools — a server that reads other servers.

Inward-facing on purpose: the thing this plugin measures is what a surface tells a cold caller, so
it ships a surface and holds itself to the same standard. Read this file's `instructions=` block
below; if this server had none, the plugin would be failing its own axis A.

Every tool drives one of the scripts beside it, as a subprocess, with the same arguments the skill
tells a person to type. Two surfaces, one implementation.

The headless trial is deliberately NOT a tool here. It spawns a real agent, spends real money and
takes minutes; a tool that quietly does that is the opposite of legible. `trial_command` returns
the exact line to run instead, so the spend is always a human's keystroke.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "legibility-audit" / "scripts"
TIMEOUT = 120

mcp = FastMCP(
    "legibility",
    version="0.1.0",
    instructions=(
        "Audits an MCP server and its repository for legibility on connect: what a cold agent "
        "receives before it acts, and how much domain knowledge it must already hold to succeed "
        "(optimum: none).\n\n"
        "Start with audit_repo(path) for everything at once. connect_snapshot and repo_inventory "
        "are the halves if you want them separately.\n\n"
        "This server does NOT run the headless trial, which is the only step that produces "
        "evidence rather than inspection — it spends money and takes minutes, so trial_command "
        "returns the line for a human to run. A report without a trial is a lint, and should say "
        "so.\n\n"
        "Scores and the meaning of each level are in skills/legibility-audit/references/rubric.md; "
        "`Prior` is the axis that matters and lower is better on it."
    ),
    # Dogfood: this plugin's own skills are served over the wire, because a tool that reports
    # "your guidance is unreachable" while hiding its own would be failing its own axis A.
    # `supporting_files` defaults to "template", which IS progressive disclosure — a client sees
    # SKILL.md and the manifest in list_resources(), then reads the manifest to decide what else
    # to fetch. Verified against fastmcp 3.4.7.
    providers=[SkillsDirectoryProvider(roots=ROOT / "skills")],
)


class Refused(Exception):
    """A script refused by name. Carried to the caller as a value, never as a traceback."""


def _run(script: str, *args: str) -> str:
    """Run one audit script and return its stdout, or refuse with what it actually said."""
    run = subprocess.run(  # noqa: S603
        ["uv", "run", "--script", str(SCRIPTS / script), *args],
        capture_output=True, text=True, timeout=TIMEOUT,
    )
    if run.returncode != 0:
        raise Refused((run.stderr or run.stdout).strip()[:2000] or f"{script} exited {run.returncode}")
    return run.stdout


@mcp.tool()
def connect_snapshot(repo: str) -> dict:
    """What a cold MCP client receives from the server in `repo`: initialize payload and tools/list.

    Static — reads the server source, so it needs no credentials, no running server and no network.
    Returns the surface plus the connect-axis findings, worst first. The single most common finding
    is a missing `instructions=` block, which is also the cheapest thing to fix.
    """
    try:
        return json.loads(_run("probe_connect.py", "--repo", repo, "--json"))
    except Refused as exc:
        return {"refused": str(exc)}


@mcp.tool()
def repo_inventory(repo: str) -> dict:
    """Skills, supporting files, cross-links and stated workflow ordering in `repo`.

    The finding that matters here is the count at the end: how many files of guidance the repo
    holds, against how many a remote caller can actually reach (zero, unless the server declares a
    skills provider).
    """
    try:
        return json.loads(_run("inventory_repo.py", "--repo", repo, "--json"))
    except Refused as exc:
        return {"refused": str(exc)}


@mcp.tool()
def audit_repo(repo: str) -> dict:
    """Both static halves at once, with the findings merged — the usual entry point.

    Does NOT include the headless trial; `trial_command` gives you that. A report built on this
    alone is inspection, not evidence, and the `Prior` axis cannot be scored from it.
    """
    connect = connect_snapshot(repo)
    inventory = repo_inventory(repo)
    findings = list(connect.get("findings", [])) + list(inventory.get("findings", []))
    # Reconcile the halves. The inventory script cannot see the server and states reachability
    # conditionally ("unless the server declares a skills provider"); this function CAN see both,
    # so it resolves the condition rather than shipping two findings that read as contradicting
    # each other. An audit tool whose own report argues with itself teaches the wrong lesson.
    providers = (connect.get("surface") or {}).get("providers") or []
    if any("Skills" in p for p in providers):
        findings = [
            f.replace(
                "Unless the server declares a skills provider, a remote caller reads ZERO of them.",
                "A skills provider IS declared, so a remote caller can reach them over the wire.",
            )
            for f in findings
        ]
    return {
        "connect": connect.get("surface"),
        "inventory": inventory.get("inventory"),
        "findings": findings,
        "trial_run": False,
        "note": (
            "Static only. The Prior axis — how much domain knowledge an agent must already hold — "
            "cannot be scored without a headless trial; call trial_command for the line to run."
        ),
    }


@mcp.tool()
def trial_command(repo: str, task: str, seed: str = "", model: str = "sonnet") -> dict:
    """The exact command that runs the headless trial. Returned, never executed.

    The trial spawns a real agent against the target MCP with file and shell tools disallowed and
    `--strict-mcp-config`, so it cannot read the repository. That isolation is the experiment: a
    remote caller cannot read your skills either, and the gap between those two situations is what
    the audit measures.
    """
    cmd = [
        "uv", "run", "--script", str(SCRIPTS / "headless_trial.py"),
        "--repo", repo, "--model", model, "--task", task,
    ]
    if seed:
        cmd += ["--seed", seed]
    return {
        "command": " ".join(json.dumps(c) if " " in c else c for c in cmd),
        "spends": "yes — a real agent runs; budget a few tens of cents per trial",
        "read_for": [
            "guessed a value the server never offered",
            "stalled or asked for something it could not discover",
            "succeeded by accident — right call, wrong reason",
            "invented a fact and reported it confidently",
            "hit an error and could not recover",
        ],
    }


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        print(json.dumps(audit_repo(str(ROOT))["findings"], indent=2))
    else:
        mcp.run()
