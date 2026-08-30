"""Regression tests for the contributing-clanker community trust boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/community/contributing-clanker"
SKILLS = PLUGIN / "skills"


class ContributingClankerPortabilityTests(unittest.TestCase):
    def test_authority_is_split_into_three_skills(self) -> None:
        expected = {"contribute", "contribute-prepare", "contribute-publish"}
        actual = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
        self.assertEqual(actual, expected)

    def test_default_skill_is_read_only_and_has_no_load_time_shell(self) -> None:
        text = (SKILLS / "contribute/SKILL.md").read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        for forbidden in ("  - Write", "  - Edit", "  - Task", "Bash(npm:*)", "Bash(pnpm:*)"):
            self.assertNotIn(forbidden, frontmatter)
        self.assertNotIn("```!", text)
        self.assertIn("Do not run prompt-load or activation-time shell commands", text)

    def test_no_automatic_persistence_hooks_exist(self) -> None:
        self.assertFalse((PLUGIN / "hooks/install.sh").exists())
        self.assertFalse((PLUGIN / "hooks/uninstall.sh").exists())

    def test_no_hidden_format_characters_or_personal_layouts(self) -> None:
        forbidden_codepoints = {0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF}
        forbidden_paths = (
            "~/000-projects/contributing-clanker",
            "$HOME/000-projects/contributing-clanker",
            "~/.contribute-system",
            "$HOME/.contribute-system",
            "~/.claude/",
            "${CLAUDE_SKILL_DIR}",
        )
        foreign_authority_markers = ("@scout", "@researcher", "CLAUDE.md")
        for path in PLUGIN.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            hidden = sorted({f"U+{ord(char):04X}" for char in text if ord(char) in forbidden_codepoints})
            self.assertFalse(hidden, f"{path}: hidden characters {hidden}")
            for forbidden in forbidden_paths:
                self.assertNotIn(forbidden, text, f"{path}: personal path {forbidden}")
            for marker in foreign_authority_markers:
                self.assertNotIn(marker, text, f"{path}: foreign authority marker {marker}")

    def test_versions_match_manifest(self) -> None:
        manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "0.9.0")
        for skill in SKILLS.glob("*/SKILL.md"):
            self.assertIn('version: "0.9.0"', skill.read_text(encoding="utf-8"), str(skill))

    def test_setup_requires_explicit_safe_paths(self) -> None:
        setup = SKILLS / "contribute-prepare/scripts/setup.sh"
        missing = subprocess.run(["bash", str(setup)], text=True, capture_output=True, check=False)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("state-dir is required", missing.stderr)

        root = subprocess.run(
            ["bash", str(setup), "--state-dir", "/", "--workspace-dir", "/tmp/contribute-work"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(root.returncode, 0)
        self.assertIn("state-dir cannot be /", root.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "profile-state"
            workspace = Path(tmp) / "worktrees"
            created = subprocess.run(
                [
                    "bash",
                    str(setup),
                    "--state-dir",
                    str(state),
                    "--workspace-dir",
                    str(workspace),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertTrue((state / "candidates").is_dir())
            self.assertTrue((state / "research").is_dir())
            self.assertTrue((state / "user-gates").is_dir())
            self.assertTrue(workspace.is_dir())

    def test_runtime_refuses_implicit_state(self) -> None:
        runner = SKILLS / "contribute-prepare/scripts/gate-runner.sh"
        env = os.environ.copy()
        env.pop("CONTRIBUTE_STATE_DIR", None)
        env.pop("CONTRIBUTE_WORKSPACE_DIR", None)
        result = subprocess.run(
            ["bash", str(runner), "open→shortlist", "/does/not/exist"],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONTRIBUTE_STATE_DIR must be explicitly set", result.stderr)

    def test_prepare_forbids_github_mutation_and_publish_requires_approval(self) -> None:
        prepare = (SKILLS / "contribute-prepare/SKILL.md").read_text(encoding="utf-8")
        publish = (SKILLS / "contribute-publish/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Never call GitHub mutation", prepare)
        self.assertIn("No external action has been taken", prepare)
        self.assertIn("fresh human approval", " ".join(publish.split()))
        self.assertIn("Earlier blanket permission", publish)


if __name__ == "__main__":
    unittest.main()
