# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Inventory a repository's skills and the workflow order they claim — and who can reach it.

Two questions, and the second is the one that bites:

1. What skills, references and processes exist, and what points at what?
2. **For every ordering rule stated in prose, what enforces it?** A workflow that lives only in a
   SKILL.md is not a workflow for a caller who never reads SKILL.md — which is every remote MCP
   client, since files do not cross the wire.

    inventory_repo.py --repo <path> [--json]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ORDER_WORDS = re.compile(
    r"\b(first|before|after|then|next|step \d|in this order|never before|"
    r"once .{0,30} has|prerequisite|must .{0,20}(precede|follow))\b",
    re.IGNORECASE,
)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def _frontmatter(text: str) -> dict[str, str]:
    """The skill's YAML-ish frontmatter, flat keys only — no yaml dependency for one field."""
    m = FRONTMATTER.match(text)
    if not m:
        return {}
    out, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^\w[\w-]*:", line):
            key, _, val = line.partition(":")
            out[key.strip()] = val.strip()
        elif key and line.strip():
            out[key] += " " + line.strip()
    return out


def inventory(repo: Path) -> dict:
    """Every skill under `repo`, its references, its cross-links and its ordering claims."""
    skills = {}
    for skill_md in sorted(repo.glob("skills/*/SKILL.md")):
        name = skill_md.parent.name
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
        fm = _frontmatter(text)
        files = sorted(
            str(p.relative_to(skill_md.parent))
            for p in skill_md.parent.rglob("*")
            if p.is_file() and p.name != "SKILL.md"
        )
        body = text[len(FRONTMATTER.match(text).group(0)):] if FRONTMATTER.match(text) else text
        skills[name] = {
            "description_chars": len(fm.get("description", "")),
            "body_lines": len(body.splitlines()),
            "supporting_files": files,
            "ordering_claims": sorted({m.group(0).lower() for m in ORDER_WORDS.finditer(body)}),
            "links_to_skills": sorted({
                s for s in re.findall(r"(?:\.\./|skills/)([a-z0-9-]+)/", body) if s != name
            }),
        }
    # a process is any executable or rendered script the repo asks a reader to run
    scripts = sorted(
        str(p.relative_to(repo)) for p in repo.rglob("*.py")
        if "scripts" in p.parts and ".venv" not in p.parts
    )
    return {"skills": skills, "scripts": scripts}


def findings(inv: dict) -> list[str]:
    """Workflow- and disclosure-axis findings — see references/rubric.md axes C and D."""
    out = []
    skills = inv["skills"]
    if not skills:
        return ["NO SKILLS FOUND — nothing to be unreachable, and nothing to orient a caller."]

    ordered = {n: s for n, s in skills.items() if s["ordering_claims"]}
    if ordered:
        out.append(
            "ORDERING STATED IN PROSE ONLY (nothing here enforces it, and none of it crosses an "
            "MCP wire): "
            + "; ".join(f"{n} [{', '.join(s['ordering_claims'][:4])}]" for n, s in ordered.items())
        )
    thick = [n for n, s in skills.items() if s["body_lines"] > 120]
    if thick:
        out.append(
            f"FRONT DOOR MAY BE A WALL — SKILL.md over 120 lines: {', '.join(thick)}. "
            "A front door that must be read in full is not progressive disclosure."
        )
    flat = [n for n, s in skills.items() if not s["supporting_files"]]
    if flat:
        out.append(
            f"NO DEPTH TO DISCLOSE — skills with no supporting files: {', '.join(flat)}. "
            "Everything they say, they say at once."
        )
    isolated = [n for n, s in skills.items() if not s["links_to_skills"]]
    if len(skills) > 1 and isolated:
        out.append(
            f"UNLINKED SKILLS (a reader landing here learns nothing about the rest): "
            f"{', '.join(isolated)}"
        )
    total = sum(len(s["supporting_files"]) + 1 for s in skills.values())
    out.append(
        f"REACHABILITY: {len(skills)} skills / {total} files of guidance in the repo. "
        "Unless the server declares a skills provider, a remote caller reads ZERO of them."
    )
    return out


def main() -> int:
    """Print the inventory and the workflow/disclosure findings."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    inv = inventory(args.repo)
    if args.json:
        print(json.dumps({"inventory": inv, "findings": findings(inv)}, indent=2))
        return 0
    print(f"=== skills in {args.repo} ===")
    for name, s in inv["skills"].items():
        print(f"\n  {name}  ({s['body_lines']} body lines, {len(s['supporting_files'])} supporting)")
        for f in s["supporting_files"]:
            print(f"      - {f}")
        if s["links_to_skills"]:
            print(f"      -> links to: {', '.join(s['links_to_skills'])}")
        if s["ordering_claims"]:
            print(f"      !! ordering claimed: {', '.join(s['ordering_claims'][:6])}")
    print(f"\n=== scripts ({len(inv['scripts'])}) ===")
    for s in inv["scripts"]:
        print(f"  {s}")
    print("\n=== findings (workflow + disclosure axes) ===")
    for i, f in enumerate(findings(inv), 1):
        print(f"  {i}. {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
