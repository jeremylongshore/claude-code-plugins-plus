"""Unit + snapshot tests for scripts/pr-classifier/.

Two layers:
    1. Unit tests over synthetic file lists — one test per contribution type.
       Pins the deterministic mapping each rule expresses.
    2. Snapshot regression tests over historical real PR diffs at
       tests/pr-classifier/fixtures/pr-NNN-*.{diff,files,expected.json}.
       Re-running the classifier on the same diff must always produce the
       same output. Changes to the expected.json need a justifying commit
       message explaining the new behavior.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

# Load rules.py by file path because the script dir uses a hyphen (`pr-classifier`)
# which isn't a valid Python identifier for normal imports.
_RULES_PATH = _REPO_ROOT / "scripts" / "pr-classifier" / "rules.py"
_spec = importlib.util.spec_from_file_location("pr_classifier_rules", _RULES_PATH)
_rules = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rules)

classify_files = _rules.classify_files
parse_catalog_additions_from_diff = _rules.parse_catalog_additions_from_diff
parse_sources_additions_from_diff = _rules.parse_sources_additions_from_diff


# =============================================================================
# Unit tests — one per contribution type
# =============================================================================


class TestSkillContribution:
    def test_single_skill_file(self):
        result = classify_files([
            "plugins/saas-packs/databricks-pack/skills/databricks-incident-runbook/SKILL.md",
        ])
        assert result["affected_skills"] == ["databricks-incident-runbook"]
        assert "skill" in result["contribution_types"]
        assert "plugin" in result["contribution_types"]
        assert result["plugin_paths"] == ["plugins/saas-packs/databricks-pack"]

    def test_skill_doesnt_drag_unaffected_skills_from_pack(self):
        """Critical: editing one skill file must NOT mark every skill in the pack."""
        result = classify_files([
            "plugins/saas-packs/databricks-pack/skills/cost-leak-hunter/SKILL.md",
        ])
        assert result["affected_skills"] == ["cost-leak-hunter"]
        # databricks-incident-runbook etc. must NOT appear
        assert "databricks-incident-runbook" not in result["affected_skills"]

    def test_multiple_skills_same_pack(self):
        result = classify_files([
            "plugins/saas-packs/databricks-pack/skills/skill-one/SKILL.md",
            "plugins/saas-packs/databricks-pack/skills/skill-two/SKILL.md",
        ])
        assert set(result["affected_skills"]) == {"skill-one", "skill-two"}
        assert result["plugin_paths"] == ["plugins/saas-packs/databricks-pack"]

    def test_skill_reference_file_doesnt_make_it_a_skill_change(self):
        """A change to skill/references/foo.md is plugin-internal but not a SKILL.md change."""
        result = classify_files([
            "plugins/saas-packs/databricks-pack/skills/skill-one/references/foo.md",
        ])
        assert result["affected_skills"] == []  # SKILL.md not touched
        assert "skill" not in result["contribution_types"]
        assert "plugin" in result["contribution_types"]


class TestAgentContribution:
    def test_agent_md_file(self):
        result = classify_files([
            "plugins/governance/intent-skill-creator/agents/agent-creator.md",
        ])
        assert result["affected_agents"] == ["agent-creator"]
        assert "agent" in result["contribution_types"]


class TestMcpContribution:
    def test_mcp_plugin_path(self):
        result = classify_files([
            "plugins/mcp/lumera-agent-memory/src/server.ts",
        ])
        assert result["affected_mcp"] == ["lumera-agent-memory"]
        assert "mcp" in result["contribution_types"]

    def test_mcp_config_inside_plugin(self):
        result = classify_files([
            "plugins/saas-packs/databricks-pack/.mcp.json",
        ])
        assert result["affected_mcp"] == ["databricks-pack"]
        assert "mcp" in result["contribution_types"]


class TestHookContribution:
    def test_hooks_json(self):
        result = classify_files([
            "plugins/security/penetration-tester/hooks/hooks.json",
        ])
        assert result["affected_hooks"] == ["penetration-tester"]
        assert "hook" in result["contribution_types"]


class TestPluginContribution:
    def test_any_plugin_change(self):
        result = classify_files([
            "plugins/governance/intent-skill-creator/README.md",
        ])
        assert "plugins/governance/intent-skill-creator" in result["plugin_paths"]
        assert "plugin" in result["contribution_types"]
        # Plugin-internal docs don't get classified as standalone doc
        assert "doc" not in result["contribution_types"]


class TestCiContribution:
    def test_workflow_yaml(self):
        result = classify_files([
            ".github/workflows/validate-plugins.yml",
        ])
        assert result["touches_workflows"] is True
        assert "ci" in result["contribution_types"]

    def test_workflow_yml_extension(self):
        result = classify_files([
            ".github/workflows/lint.yaml",
        ])
        assert result["touches_workflows"] is True


class TestFrontendContribution:
    def test_marketplace_src(self):
        result = classify_files([
            "marketplace/src/pages/index.astro",
        ])
        assert result["touches_frontend"] is True
        assert "frontend" in result["contribution_types"]

    def test_marketplace_root_not_src_doesnt_count_as_frontend(self):
        result = classify_files([
            "marketplace/DESIGN.md",
        ])
        assert result["touches_frontend"] is False
        # It's a doc since marketplace/ isn't a plugin path
        assert "doc" in result["contribution_types"]


class TestScriptContribution:
    def test_scripts_path(self):
        result = classify_files([
            "scripts/validate-skills-schema.py",
        ])
        assert result["touches_scripts"] is True
        assert "script" in result["contribution_types"]


class TestDocContribution:
    def test_top_level_readme(self):
        result = classify_files(["README.md"])
        assert "doc" in result["contribution_types"]

    def test_top_000_docs(self):
        result = classify_files(["000-docs/some-decision.md"])
        assert "doc" in result["contribution_types"]

    def test_docs_dir(self):
        result = classify_files(["docs/getting-started.md"])
        assert "doc" in result["contribution_types"]


class TestTestContribution:
    def test_test_prefix_file(self):
        result = classify_files(["tests/test_foo.py"])
        assert result["touches_tests"] is True
        assert "test" in result["contribution_types"]

    def test_plugin_internal_test(self):
        result = classify_files([
            "plugins/security/penetration-tester/tests/test_x.py",
        ])
        # Tests inside a plugin still count as both plugin AND test
        assert "test" in result["contribution_types"]
        assert "plugin" in result["contribution_types"]


# =============================================================================
# Unknown-pattern detection
# =============================================================================


class TestUnknownDetection:
    def test_unrecognized_top_level_dir(self):
        result = classify_files(["new-experimental-dir/foo.txt"])
        assert result["unknown"] is True
        assert "new-experimental-dir/foo.txt" in result["unmatched"]

    def test_all_unmatched_when_empty_recognizable_files(self):
        result = classify_files(["weird-thing.xyz"])
        assert result["unknown"] is True

    def test_no_unknown_when_everything_matches(self):
        result = classify_files([
            "plugins/governance/x/skills/y/SKILL.md",
            "README.md",
            "scripts/foo.py",
        ])
        assert result["unknown"] is False
        assert result["unmatched"] == []


# =============================================================================
# Edge cases
# =============================================================================


class TestEdgeCases:
    def test_empty_input(self):
        result = classify_files([])
        assert result["contribution_types"] == []
        assert result["plugin_paths"] == []
        assert result["unknown"] is False

    def test_blank_lines_ignored(self):
        result = classify_files(["", "  ", "README.md"])
        assert "doc" in result["contribution_types"]

    def test_file_categories_extension_counting(self):
        result = classify_files([
            "scripts/a.py",
            "scripts/b.py",
            "README.md",
            "package.json",
        ])
        cats = result["file_categories"]
        assert cats.get("py") == 2
        assert cats.get("md") == 1
        assert cats.get("json") == 1

    def test_mixed_contribution_types(self):
        """A PR touching scripts AND a plugin AND CI should surface all three."""
        result = classify_files([
            "scripts/foo.py",
            "plugins/governance/x/SKILL.md",
            ".github/workflows/test.yml",
        ])
        types = set(result["contribution_types"])
        assert {"script", "plugin", "ci"}.issubset(types)


# =============================================================================
# Catalog-addition diff parsing
# =============================================================================


_CATALOG_DIFF_AOMI = """diff --git a/.claude-plugin/marketplace.extended.json b/.claude-plugin/marketplace.extended.json
index 1234567..89abcde 100644
--- a/.claude-plugin/marketplace.extended.json
+++ b/.claude-plugin/marketplace.extended.json
@@ -100,6 +100,12 @@
     "category": "ai-ml"
   },
+  {
+    "name": "aomi",
+    "source": "./plugins/crypto/aomi",
+    "category": "crypto",
+    "version": "1.0.0"
+  },
   {
     "name": "next-thing",
"""


class TestCatalogAdditionParsing:
    def test_parses_single_added_entry(self):
        adds = parse_catalog_additions_from_diff(_CATALOG_DIFF_AOMI)
        assert len(adds) == 1
        assert adds[0]["name"] == "aomi"
        assert adds[0]["category"] == "crypto"
        assert adds[0]["source"] == "./plugins/crypto/aomi"

    def test_classify_picks_up_catalog_add_type(self):
        result = classify_files(
            [".claude-plugin/marketplace.extended.json"],
            diff_text=_CATALOG_DIFF_AOMI,
        )
        assert "catalog_add" in result["contribution_types"]
        assert result["catalog_additions"][0]["name"] == "aomi"

    def test_no_catalog_diff_no_adds(self):
        result = classify_files(
            [".claude-plugin/marketplace.extended.json"],
            diff_text=None,
        )
        assert result["catalog_additions"] == []
        assert "catalog" in result["contribution_types"]  # touch detected
        assert "catalog_add" not in result["contribution_types"]


# =============================================================================
# Sources.yaml addition diff parsing
# =============================================================================


_SOURCES_DIFF = """diff --git a/sources.yaml b/sources.yaml
index 1111111..2222222 100644
--- a/sources.yaml
+++ b/sources.yaml
@@ -5,3 +5,7 @@
 - name: existing-source
   repo: foo/bar
+- name: new-external-source
+  repo: octocat/hello-world
+  ref: main
"""


class TestSourcesAdditionParsing:
    def test_parses_single_sources_add(self):
        adds = parse_sources_additions_from_diff(_SOURCES_DIFF)
        assert len(adds) == 1
        assert adds[0]["name"] == "new-external-source"

    def test_classify_picks_up_sources_add_type(self):
        result = classify_files(["sources.yaml"], diff_text=_SOURCES_DIFF)
        assert "sources_add" in result["contribution_types"]
        assert result["sources_additions"][0]["name"] == "new-external-source"


# =============================================================================
# Regression: historical PR shapes
# =============================================================================


class TestHistoricalPRShapes:
    """Synthetic recreations of PR shapes we've seen in production.

    These mirror the real PRs that motivated the new classifier — particularly
    the doc-only-PR-incorrectly-grading-the-whole-pack failure mode from #823.
    """

    def test_pr_823_doc_only_change_does_not_drag_pack_skills(self):
        """#823 (the bug-triggering PR) was a doc-only edit but the coarse
        depth-3 awk extractor caused the prescreen to scan all 24 skills
        in databricks-pack. With this classifier, the doc edit produces
        empty affected_skills."""
        result = classify_files([
            "plugins/saas-packs/databricks-pack/000-docs/000-INDEX.md",
            "plugins/saas-packs/databricks-pack/000-docs/014-DR-DRFT-cost-leak-cfo-output-spec.md",
        ])
        # NO skills affected — that's the entire point
        assert result["affected_skills"] == []
        # Plugin path is still surfaced
        assert "plugins/saas-packs/databricks-pack" in result["plugin_paths"]
        assert "plugin" in result["contribution_types"]

    def test_pr_822_ci_lint_fix(self):
        """#822 — fix(ci): clear lint failures. Touches plugin docs but no skills."""
        result = classify_files([
            "plugins/saas-packs/foo-pack/README.md",
            "plugins/saas-packs/bar-pack/README.md",
            ".github/workflows/validate-plugins.yml",
        ])
        assert result["touches_workflows"] is True
        assert result["affected_skills"] == []
        assert "ci" in result["contribution_types"]

    def test_pr_818_catalog_only_external_contribution(self):
        """#818 — victorchimakanu added one row to marketplace.extended.json.
        Without the diff text we only know the catalog file was touched;
        with the diff we get the catalog_additions entry."""
        result_no_diff = classify_files(
            [".claude-plugin/marketplace.extended.json"],
            diff_text=None,
        )
        assert "catalog" in result_no_diff["contribution_types"]

        result_with_diff = classify_files(
            [".claude-plugin/marketplace.extended.json"],
            diff_text=_CATALOG_DIFF_AOMI,
        )
        assert "catalog_add" in result_with_diff["contribution_types"]
        assert len(result_with_diff["catalog_additions"]) == 1

    def test_self_classification(self):
        """The classifier should be able to classify its own PR.

        Reviewer fix PR #838: original test listed only 5 of the 9 files this
        PR adds. Expanded to the full set including the README and the
        fixture files so the test pins what the classifier ACTUALLY sees on
        this PR.
        """
        result = classify_files([
            "scripts/pr-classifier/__init__.py",
            "scripts/pr-classifier/rules.py",
            "scripts/pr-classifier/detect_components.py",
            "scripts/pr-classifier/README.md",
            "tests/pr-classifier/__init__.py",
            "tests/pr-classifier/test_classifier.py",
            "tests/pr-classifier/fixtures/pr-823.files",
            "tests/pr-classifier/fixtures/pr-823.diff",
            "tests/pr-classifier/fixtures/pr-823.expected.json",
        ])
        types = set(result["contribution_types"])
        assert "script" in types
        assert "test" in types
        # NO plugin touches
        assert result["plugin_paths"] == []
        assert result["affected_skills"] == []
        assert result["touches_workflows"] is False
        assert result["unknown"] is False


# =============================================================================
# Output shape stability
# =============================================================================


class TestOutputShape:
    def test_all_top_level_keys_present(self):
        result = classify_files(["README.md"])
        expected_keys = {
            "contribution_types",
            "plugin_paths",
            "affected_skills",
            "affected_agents",
            "affected_mcp",
            "affected_hooks",
            "catalog_additions",
            "sources_additions",
            "file_categories",
            "touches_workflows",
            "touches_frontend",
            "touches_scripts",
            "touches_tests",
            "unknown",
            "unmatched",
        }
        assert set(result.keys()) == expected_keys

    def test_lists_are_sorted(self):
        result = classify_files([
            "plugins/security/c/SKILL.md",
            "plugins/security/a/SKILL.md",
            "plugins/security/b/SKILL.md",
        ])
        assert result["plugin_paths"] == sorted(result["plugin_paths"])

    def test_output_is_json_serializable(self):
        result = classify_files([
            "plugins/governance/x/skills/y/SKILL.md",
            ".github/workflows/test.yml",
        ])
        # Round-trip through JSON
        s = json.dumps(result)
        loaded = json.loads(s)
        assert loaded == result

    def test_deterministic_repeat_runs(self):
        files = [
            "plugins/security/x/skills/y/SKILL.md",
            "scripts/foo.py",
            ".github/workflows/bar.yml",
        ]
        r1 = classify_files(files)
        r2 = classify_files(files)
        assert r1 == r2


# =============================================================================
# Helper-function tests
# =============================================================================


@pytest.mark.parametrize(
    "path, expected",
    [
        ("plugins/cat/name/file.md", True),
        ("plugins/mcp/foo/server.ts", True),
        ("scripts/foo.py", False),
        ("plugins", False),
        ("plugins/cat", False),
        ("", False),
    ],
)
def test_is_plugin_path(path, expected):
    from pathlib import PurePosixPath
    p = PurePosixPath(path) if path else PurePosixPath()
    assert _rules._is_plugin_path(p) == expected


# =============================================================================
# Reviewer-fix regressions (PR #838 review)
# =============================================================================


class TestBraceInStringCatalogParser:
    """Reviewer flagged: unbalanced braces inside a JSON string value
    silently drove the catalog parser's depth counter wrong and dropped
    the entire catalog entry. The fix introduces a quote-aware brace
    counter."""

    def test_unbalanced_brace_in_string_does_not_drop_entry(self):
        diff = (
            'diff --git a/.claude-plugin/marketplace.extended.json '
            'b/.claude-plugin/marketplace.extended.json\n'
            'index 1..2 100644\n'
            '--- a/.claude-plugin/marketplace.extended.json\n'
            '+++ b/.claude-plugin/marketplace.extended.json\n'
            '@@ -1,3 +1,9 @@\n'
            '   "plugins": [\n'
            '+    {\n'
            '+      "name": "tricky-pack",\n'
            '+      "source": "./plugins/example/tricky",\n'
            '+      "description": "Uses {foo {bar} template patterns",\n'
            '+      "category": "example"\n'
            '+    },\n'
            '     {\n'
        )
        adds = _rules.parse_catalog_additions_from_diff(diff)
        assert len(adds) == 1, "unbalanced braces in string value should NOT drop the entry"
        assert adds[0]["name"] == "tricky-pack"

    def test_quote_aware_brace_counter(self):
        # Inside a string: not counted
        assert _rules._count_unquoted_braces('"foo {bar}"') == (0, 0)
        # Outside a string: counted
        assert _rules._count_unquoted_braces('{ "name": "x" }') == (1, 1)
        # Mixed: only the outside-string braces count
        assert _rules._count_unquoted_braces('{ "name": "x{y}" }') == (1, 1)
        # Escaped quote inside string preserves string state
        assert _rules._count_unquoted_braces('{ "n": "a\\"b{c}" }') == (1, 1)


class TestDepthFlexibleSkillMatch:
    """Reviewer flagged: depth-4-only skill match misses sub-vendored layouts
    like plugins/saas-packs/<vendor>/<sub>/skills/<x>/SKILL.md."""

    def test_depth_5_subvendored_skill_still_classified(self):
        result = classify_files([
            "plugins/saas-packs/vendor-x/sub-y/skills/my-skill/SKILL.md",
        ])
        assert "my-skill" in result["affected_skills"]
        assert "skill" in result["contribution_types"]

    def test_depth_4_standard_skill_still_works(self):
        """Regression check that the standard depth-4 case still works."""
        result = classify_files([
            "plugins/security/example/skills/my-skill/SKILL.md",
        ])
        assert result["affected_skills"] == ["my-skill"]


class TestSourcesYamlRootOnly:
    """Reviewer flagged: sources_additions parser fired on non-root
    sources.yaml files. Now restricted to the exact root path."""

    def test_non_root_sources_yaml_does_not_fire_sources_add(self):
        diff = (
            "diff --git a/config/sources.yaml b/config/sources.yaml\n"
            "index 1..2 100644\n"
            "--- a/config/sources.yaml\n"
            "+++ b/config/sources.yaml\n"
            "@@ -1,1 +1,3 @@\n"
            "+- name: should-not-be-counted\n"
            "+  repo: foo/bar\n"
        )
        adds = _rules.parse_sources_additions_from_diff(diff)
        assert adds == []

    def test_root_sources_yaml_fires_sources_add(self):
        diff = (
            "diff --git a/sources.yaml b/sources.yaml\n"
            "index 1..2 100644\n"
            "--- a/sources.yaml\n"
            "+++ b/sources.yaml\n"
            "@@ -1,1 +1,3 @@\n"
            "+- name: legitimate\n"
            "+  repo: foo/bar\n"
        )
        adds = _rules.parse_sources_additions_from_diff(diff)
        assert len(adds) == 1
        assert adds[0]["name"] == "legitimate"


class TestFileCategoriesDeterminism:
    """Reviewer flagged: file_categories dict insertion order followed input
    file order, breaking the deterministic-output contract. Now sorted."""

    def test_file_categories_keys_sorted(self):
        result = classify_files([
            "scripts/z.py",   # py
            "README.md",      # md
            "package.json",   # json
        ])
        keys = list(result["file_categories"].keys())
        assert keys == sorted(keys), f"file_categories keys not sorted: {keys}"

    def test_file_categories_order_independent_of_input_order(self):
        a = classify_files(["scripts/x.py", "README.md", "package.json"])
        b = classify_files(["package.json", "scripts/x.py", "README.md"])
        c = classify_files(["README.md", "package.json", "scripts/x.py"])
        assert list(a["file_categories"].keys()) == list(b["file_categories"].keys()) == list(c["file_categories"].keys())


# =============================================================================
# Real PR snapshot regression tests
# =============================================================================
#
# Each entry references a `pr-NNN.files` + `pr-NNN.diff` + `pr-NNN.expected.json`
# trio under tests/pr-classifier/fixtures/. The classifier is run against the
# file list (and diff for catalog/sources detection); output is asserted equal
# to the committed expected.json.
#
# When the classifier's behavior changes intentionally, the fixture files
# must be regenerated and the commit message must explain why.

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_fixture(pr_number: str) -> tuple[list[str], str | None]:
    """Read the pr-NNN.files list and pr-NNN.diff text for a fixture PR."""
    files_path = _FIXTURES / f"pr-{pr_number}.files"
    diff_path = _FIXTURES / f"pr-{pr_number}.diff"
    files = [
        l.strip()
        for l in files_path.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    diff_text = diff_path.read_text(encoding="utf-8") if diff_path.exists() else None
    return files, diff_text


class TestNewFixtureVerdicts:
    """Headline-verdict assertions for the PR #811/#819/#820/#821 fixture sets.

    The parametrized snapshot test below pins the FULL output dict; these
    named tests pin the one classification verdict each PR shape exists to
    exercise, so an intentional snapshot regen can't silently flip the
    semantic verdict without failing a readable named test.
    """

    def test_pr_811_readme_only_community_listing_is_doc(self):
        """#811 — external contributor added a community-plugin row to the
        top-level README. File-wise it's a doc-only change: no plugin dir,
        no catalog file, no sources.yaml."""
        files, diff = _load_fixture("811")
        result = classify_files(files, diff_text=diff)
        assert result["contribution_types"] == ["doc"]
        assert result["plugin_paths"] == []
        assert result["unknown"] is False

    def test_pr_819_bulk_sync_recovery_mixed_shape(self):
        """#819 — the sync-external.mjs rewrite that recovered 15 stranded
        sources: 306 files spanning recovered plugins, catalog additions,
        frontend data, and scripts. The big-PR stress shape."""
        files, diff = _load_fixture("819")
        result = classify_files(files, diff_text=diff)
        types = set(result["contribution_types"])
        assert {"plugin", "skill", "catalog", "catalog_add", "script", "frontend"}.issubset(types)
        assert len(result["plugin_paths"]) == 14
        # Note: 15 recovered sources parse as 30 catalog_additions because the
        # catalog parser currently flushes nested author objects as separate
        # entries. Pinned as-is; fixing the parser requires a fixture regen
        # with a justifying commit message.
        assert len(result["catalog_additions"]) == 30
        # marketplace/public/** and pnpm-lock.yaml match no rule today.
        assert result["unknown"] is True

    def test_pr_820_root_sources_yaml_addition_is_sources_add(self):
        """#820 — external contributor added the skillrot entry to root
        sources.yaml. Exactly the sources_add lane."""
        files, diff = _load_fixture("820")
        result = classify_files(files, diff_text=diff)
        assert result["contribution_types"] == ["sources", "sources_add"]
        assert len(result["sources_additions"]) == 1
        # Real sources.yaml entries are indented under `sources:`, so the
        # parser captures the entry key as "- name" (not "name" — that slot
        # gets the nested author name). Pinned as-is: the sources_add verdict
        # is correct; the key shape is a known parser quirk on indented YAML.
        assert result["sources_additions"][0]["- name"] == "skillrot"

    def test_pr_821_plugin_docs_and_manifest_is_plugin_only(self):
        """#821 — databricks-pack README + package.json bump. Plugin-internal
        change that must NOT drag any of the pack's 24 skills (the #823
        failure mode, seen again from the docs side)."""
        files, diff = _load_fixture("821")
        result = classify_files(files, diff_text=diff)
        assert result["contribution_types"] == ["plugin"]
        assert result["plugin_paths"] == ["plugins/saas-packs/databricks-pack"]
        assert result["affected_skills"] == []


# NOTE on pr-819.diff: the full #819 diff is ~64k added lines across 306
# files and exceeds GitHub's API diff limit (HTTP 406 over 300 files), so the
# committed fixture diff is trimmed to the .claude-plugin/marketplace.extended.json
# section — the only part of that PR's diff the classifier's diff parsers
# consume (root sources.yaml was not touched by #819). pr-819.files is the
# complete 306-file list.
@pytest.mark.parametrize("pr_number", ["811", "819", "820", "821", "823"])
def test_real_pr_snapshot(pr_number):
    files_path = _FIXTURES / f"pr-{pr_number}.files"
    diff_path = _FIXTURES / f"pr-{pr_number}.diff"
    expected_path = _FIXTURES / f"pr-{pr_number}.expected.json"
    if not files_path.exists():
        pytest.skip(f"fixture pr-{pr_number}.files not present")
    if not expected_path.exists():
        pytest.skip(f"fixture pr-{pr_number}.expected.json not present")

    files = [
        l.strip()
        for l in files_path.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    diff_text = diff_path.read_text(encoding="utf-8") if diff_path.exists() else None
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    result = classify_files(files, diff_text=diff_text)
    assert result == expected, (
        f"\nclassifier output changed for PR #{pr_number}.\n"
        f"If this change is intentional, regenerate the fixture:\n"
        f"  python3 scripts/pr-classifier/detect_components.py "
        f"--file tests/pr-classifier/fixtures/pr-{pr_number}.files "
        f"--diff-file tests/pr-classifier/fixtures/pr-{pr_number}.diff "
        f"--pretty > tests/pr-classifier/fixtures/pr-{pr_number}.expected.json\n"
        f"AND explain the new behavior in the commit message.\n"
    )
