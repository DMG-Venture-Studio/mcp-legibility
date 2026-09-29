# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Put a real agent with no domain context in front of the server and watch what it does.

The only step of the audit that produces evidence. Steps 1 and 2 read the surface; an author
cannot grade their own system's legibility, because they cannot un-know the domain. This can.

**The isolation is the experiment.** The trial agent gets the target MCP and NOTHING else:
`--strict-mcp-config` so it cannot inherit the parent session's servers, and file and shell tools
disallowed so it cannot read the repository. If it can open SKILL.md the test is void — a remote
caller cannot, and that asymmetry is exactly what is being measured.

It also runs against a COPY of the corpus in a temp directory, so a trial never writes to a live
one and two runs of the same trial start from the same state.

    headless_trial.py --repo <path> --task "..." [--seed <dir>] [--model sonnet] [--max-turns 12]
    headless_trial.py --repo <path> --task-file task.md --json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# What the trial agent must NOT have. Reading the repo would let it learn the domain out of band,
# which is the one thing this experiment exists to prevent.
BLOCKED = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch", "Task", "Agent"]


def build_mcp_config(repo: Path, corpus: Path, server_name: str) -> dict:
    """An MCP config attaching only the target server, pointed at an isolated corpus copy."""
    return {
        "mcpServers": {
            server_name: {
                "command": "uv",
                "args": ["run", "--script", str(repo / "mcp" / "server.py")],
                "env": {
                    "RECRUITING_POOL_DIR": str(corpus / "pool"),
                    "RECRUITING_BENCH_DIR": str(corpus / "profiles"),
                    "RECRUITING_JUDGMENTS": str(corpus / "judgments.jsonl"),
                    "RECRUITING_CONTRACT": str(repo / "contract.json"),
                },
            }
        }
    }


def seed_corpus(dest: Path, seed: Path | None) -> None:
    """Copy a starting corpus into the trial's temp directory, or make an empty one."""
    (dest / "pool").mkdir(parents=True, exist_ok=True)
    (dest / "profiles").mkdir(parents=True, exist_ok=True)
    if seed is None:
        return
    for sub in ("pool", "profiles"):
        src = seed / sub
        if src.is_dir():
            for f in src.glob("*.json"):
                shutil.copy2(f, dest / sub / f.name)


def run_trial(repo: Path, task: str, corpus: Path, server: str, model: str, turns: int) -> dict:
    """Run `claude -p` isolated to the target MCP; return the parsed result."""
    cfg = corpus / "mcp-config.json"
    cfg.write_text(json.dumps(build_mcp_config(repo, corpus, server)), encoding="utf-8")
    cmd = [
        "claude", "-p", task,
        "--mcp-config", str(cfg),
        "--strict-mcp-config",
        "--allowedTools", f"mcp__{server}__*",
        "--disallowedTools", *BLOCKED,
        "--output-format", "json",
        "--max-turns", str(turns),
        "--model", model,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)  # noqa: S603
    try:
        return {"ok": True, "result": json.loads(proc.stdout), "stderr": proc.stderr[-2000:]}
    except json.JSONDecodeError:
        return {"ok": False, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-2000:]}


def tells(result: dict, corpus: Path) -> list[str]:
    """Heuristic hints toward the five tells. HINTS, not verdicts — read the transcript.

    Nothing here can decide whether an agent "succeeded by accident" or "invented a fact"; those
    need a reader. What it can do is count what happened and surface the corpus side effects, so a
    reader knows where to look.
    """
    out = []
    body = json.dumps(result.get("result", result))
    ledger = corpus / "judgments.jsonl"
    wrote = ledger.exists() and ledger.read_text(encoding="utf-8").strip()
    if wrote:
        rows = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
        out.append(f"WROTE {len(rows)} ledger row(s). Check each against what the task asked for.")
        for r in rows:
            out.append(f"    {r[:220]}")
    else:
        out.append("WROTE NOTHING to the ledger.")
    for needle, note in (
        ("refused", "the surface refused at least once — was the refusal actionable?"),
        ("error", "an error surfaced — did the agent recover from it?"),
        ("unlisted", "the agent reached for `unlisted` — did anything warn it what that costs?"),
        ("warning", "a warning was returned — did the agent pass it on or absorb it?"),
    ):
        if needle in body.lower():
            out.append(f"SAW {needle!r}: {note}")
    return out


def main() -> int:
    """Run one trial and print the transcript, the corpus side effects, and the tells to read for."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--task")
    ap.add_argument("--task-file", type=Path)
    ap.add_argument("--seed", type=Path, help="a corpus to copy in before the trial")
    ap.add_argument("--server", default="target")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--max-turns", type=int, default=12)
    ap.add_argument("--keep", action="store_true", help="keep the temp corpus for inspection")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    task = args.task or (args.task_file.read_text(encoding="utf-8") if args.task_file else None)
    if not task:
        print("refused: give --task or --task-file", file=sys.stderr)
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="legibility-trial-"))
    try:
        seed_corpus(tmp, args.seed)
        res = run_trial(args.repo, task, tmp, args.server, args.model, args.max_turns)
        hints = tells(res, tmp)
        if args.json:
            print(json.dumps({"result": res, "tells": hints, "corpus": str(tmp)}, indent=2))
        else:
            print("=== task given to an agent with NO domain context ===")
            print(task.strip()[:800])
            print("\n=== what it said back ===")
            r = res.get("result", {})
            print(r.get("result", res.get("stdout", "(no parseable output)"))[:4000])
            print(f"\n  turns={r.get('num_turns')}  cost_usd={r.get('total_cost_usd')}  "
                  f"is_error={r.get('is_error')}")
            print("\n=== corpus side effects and tells ===")
            for h in hints:
                print(f"  {h}")
            print("\n=== now read the transcript for the five tells ===")
            print("  guessed a value | stalled | succeeded by accident | invented a fact | "
                  "could not recover from an error")
        if args.keep:
            print(f"\ncorpus kept at {tmp}")
        return 0
    finally:
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
