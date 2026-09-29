"""Tests over the static audit scripts and the server self-test.

The two scripts have no dependencies beyond the standard library, so they run
under the current interpreter. The server needs fastmcp, so its self-test runs
through `uv run --script` and is skipped, with a stated reason, when `uv` is not
on the path. Nothing here runs the headless trial: it spends money.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "legibility-audit" / "scripts"


def run_script(name: str, *args: str) -> dict:
    """Run one static script with --json and parse its output."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args, "--json"],
        capture_output=True, text=True, timeout=120, check=True,
    )
    return json.loads(proc.stdout)


class ProbeConnect(unittest.TestCase):
    """What a cold client receives from this repo's own server."""

    def setUp(self) -> None:
        self.out = run_script("probe_connect.py", "--repo", str(ROOT))
        self.surface = self.out["surface"]

    def test_instructions_name_an_entry_point(self) -> None:
        self.assertIn("Start with", self.surface["instructions"])

    def test_instructions_state_a_non_goal(self) -> None:
        self.assertIn("does NOT run the headless trial", self.surface["instructions"])

    def test_tools_in_registration_order(self) -> None:
        names = [t["name"] for t in self.surface["tools"]]
        self.assertEqual(names, ["connect_snapshot", "repo_inventory", "audit_repo", "trial_command"])

    def test_every_tool_is_described(self) -> None:
        self.assertTrue(all(t["has_description"] for t in self.surface["tools"]))

    def test_skills_provider_is_declared_and_recognised(self) -> None:
        self.assertTrue(any("Skills" in p for p in self.surface["providers"]))
        self.assertTrue(any(f.startswith("OK: a skills provider is declared") for f in self.out["findings"]))

    def test_refuses_when_no_server_exists(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "probe_connect.py"), "--repo", str(ROOT / "tests")],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("refused", proc.stderr)


class InventoryRepo(unittest.TestCase):
    """Skills, supporting files, ordering claims and reachability."""

    def setUp(self) -> None:
        self.out = run_script("inventory_repo.py", "--repo", str(ROOT))
        self.skills = self.out["inventory"]["skills"]

    def test_one_skill_with_its_supporting_files(self) -> None:
        self.assertEqual(list(self.skills), ["legibility-audit"])
        files = self.skills["legibility-audit"]["supporting_files"]
        self.assertIn("references/rubric.md", files)
        self.assertIn("templates/instructions-block.md", files)
        self.assertGreaterEqual(len(files), 9)

    def test_ordering_claims_are_detected(self) -> None:
        self.assertIn("first", self.skills["legibility-audit"]["ordering_claims"])

    def test_reachability_finding_is_conditional(self) -> None:
        reach = [f for f in self.out["findings"] if f.startswith("REACHABILITY")]
        self.assertEqual(len(reach), 1)
        self.assertIn("Unless the server declares a skills provider", reach[0])

    def test_three_scripts_listed(self) -> None:
        self.assertEqual(len(self.out["inventory"]["scripts"]), 3)


class ServerSelfTest(unittest.TestCase):
    """The server audits this repository through its own tools."""

    @unittest.skipUnless(shutil.which("uv"), "uv is not on the path; the server needs it for fastmcp")
    def test_audit_repo_reconciles_reachability(self) -> None:
        proc = subprocess.run(
            ["uv", "run", "--script", str(ROOT / "mcp" / "server.py"), "--selftest"],
            capture_output=True, text=True, timeout=600,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        findings = json.loads(proc.stdout)
        self.assertIsInstance(findings, list)
        joined = "\n".join(findings)
        self.assertIn("A skills provider IS declared", joined)
        self.assertNotIn("reads ZERO of them", joined)


if __name__ == "__main__":
    unittest.main()
