"""Path-routing dry-run tests for the CI workflow set.

The 2026-07 consolidation retired the split lint workflows (lint-markdown /
lint-python / lint-shell / lint-typescript / lint-skill-codeblocks); their jobs
now run inside the UNFILTERED "Validate Plugins" workflow, which fires on every
PR. So lint coverage is no longer path-routed — it runs unconditionally, which
is what fixes the "N Expected forever" stuck-PR class. These tests pin the new
invariant; the glob / paths-ignore / YAML-extraction tests below are
architecture-independent library tests.

Pin which workflows fire for synthetic PR diffs. Catches:
    - Glob typos in a workflow's `paths:` filter
    - Renamed file patterns that no workflow catches
    - Workflows that should fire NEVER firing
    - Workflows that should NOT fire firing erroneously

Tests document the intended routing as concrete assertions. Changes to the
routing require updating the test + an accompanying commit message
explaining why.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

_SCRIPT_PATH = _REPO_ROOT / "scripts" / "ci" / "check_path_routing.py"
_spec = importlib.util.spec_from_file_location("check_path_routing", _SCRIPT_PATH)
_routing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_routing)

run_routing = _routing.run_routing
list_all_workflows = _routing.list_all_workflows
path_matches_filter = _routing.path_matches_filter
extract_workflow_metadata = _routing.extract_workflow_metadata
workflow_fires_for = _routing.workflow_fires_for


# =============================================================================
# Helpers
# =============================================================================


def fires_for(files: list[str]) -> set[str]:
    """Return the set of workflow names that match for a given file list,
    EXCLUDING workflows that fire on every PR (no paths filter)."""
    result = run_routing(files)
    return {k for k in result.keys() if not k.startswith("_")}


# =============================================================================
# Lint consolidation (2026-07)
# =============================================================================

RETIRED_LINT_WORKFLOWS = {
    "Lint Markdown",
    "Lint Python",
    "Lint Shell",
    "Lint TypeScript",
    "Lint Skill Code Blocks",
}


def all_workflow_names() -> set[str]:
    return {wf["name"] for wf in list_all_workflows()}


def validate_plugins_fires(files: list[str]) -> bool:
    """Validate Plugins is unfiltered → fires on every PR → lint coverage runs."""
    return "Validate Plugins" in run_routing(files)["_no_filter"]


class TestLintConsolidation:
    """The split lint workflows were retired; their jobs run inside the
    unfiltered Validate Plugins workflow, so lint runs on every PR without
    path-routing fragility."""

    def test_split_lint_workflows_are_retired(self):
        present = all_workflow_names()
        for name in RETIRED_LINT_WORKFLOWS:
            assert name not in present, (
                f"'{name}' should have been consolidated into Validate Plugins, "
                f"not left as a standalone path-filtered workflow"
            )

    def test_validate_plugins_covers_every_change_kind(self):
        # A markdown, python, typescript, shell, or skill change is all covered
        # by the unfiltered Validate Plugins run (which carries the lint jobs).
        for files in (
            ["README.md"],
            ["scripts/foo.py"],
            ["plugins/security/penetration-tester/pyproject.toml"],
            ["plugins/x/requirements.txt"],
            ["packages/cli/src/index.ts"],
            ["scripts/sync-marketplace.cjs"],
            ["packages/cli/tsconfig.json"],
            ["package.json"],
            ["scripts/quick-test.sh"],
            ["plugins/security/penetration-tester/skills/x/SKILL.md"],
            ["plugins/security/penetration-tester/README.md"],
        ):
            assert validate_plugins_fires(files), (
                f"Validate Plugins must fire (carry lint) for {files}"
            )

    def test_no_retired_lint_workflow_fires_for_any_change(self):
        for files in (
            ["README.md"],
            ["scripts/foo.py"],
            ["packages/cli/src/index.ts"],
            ["scripts/quick-test.sh"],
            ["plugins/security/penetration-tester/skills/x/SKILL.md"],
        ):
            assert RETIRED_LINT_WORKFLOWS.isdisjoint(fires_for(files)), (
                f"a retired lint workflow unexpectedly fired for {files}"
            )


class TestActionlintRouting:
    def test_workflow_change_fires_actionlint(self):
        fired = fires_for([".github/workflows/some-workflow.yml"])
        assert "Actionlint" in fired

    def test_non_workflow_change_does_not_fire_actionlint(self):
        fired = fires_for(["README.md"])
        assert "Actionlint" not in fired


# =============================================================================
# Multi-file routing
# =============================================================================


class TestMultiFileRouting:
    def test_mixed_code_change_is_covered_by_validate_plugins(self):
        files = ["scripts/foo.py", "packages/cli/src/x.ts"]
        assert validate_plugins_fires(files)
        assert RETIRED_LINT_WORKFLOWS.isdisjoint(fires_for(files))

    def test_doc_only_pr_gets_lint_but_does_not_fire_actionlint(self):
        """A doc-only edit is still linted (via the unfiltered Validate Plugins
        run), but no code/workflow-specific path-filtered workflow (Actionlint)
        fires for it."""
        files = [
            "plugins/saas-packs/databricks-pack/000-docs/000-INDEX.md",
            "plugins/saas-packs/databricks-pack/000-docs/014-spec.md",
        ]
        assert validate_plugins_fires(files)
        assert "Actionlint" not in fires_for(files)


# =============================================================================
# Each new workflow has a paths filter
# =============================================================================


class TestPathFilteredWorkflowsHaveFilters:
    """After the lint consolidation, Actionlint is the remaining path-filtered
    lint-adjacent workflow (it should fire only on workflow/config changes, not
    every PR). If it loses its filter and starts firing on every PR — or goes
    missing — this catches it."""

    EXPECTED_FILTERED_WORKFLOWS = {
        "Actionlint",
    }

    def test_expected_workflows_are_present_and_filtered(self):
        all_wfs = list_all_workflows()
        names = {wf["name"] for wf in all_wfs}
        for expected in self.EXPECTED_FILTERED_WORKFLOWS:
            assert expected in names, f"expected workflow '{expected}' is missing"
        for wf in all_wfs:
            if wf["name"] in self.EXPECTED_FILTERED_WORKFLOWS:
                assert wf["paths"], (
                    f"workflow '{wf['name']}' ({wf['file']}) should have a "
                    f"paths: filter but does not"
                )


# =============================================================================
# Glob-matching unit tests
# =============================================================================


@pytest.mark.parametrize(
    "path, patterns, expected",
    [
        ("README.md", ["**/*.md"], True),
        ("scripts/foo.py", ["**/*.py"], True),
        ("scripts/foo.py", ["**/*.ts"], False),
        ("packages/cli/tsconfig.json", ["**/tsconfig*.json"], True),
        ("plugins/x/y/SKILL.md", ["plugins/**/SKILL.md"], True),
        (".github/workflows/test.yml", [".github/workflows/**"], True),
        ("README.md", ["**/*.py", "**/*.md"], True),
        ("README.md", ["**/*.py", "**/*.ts"], False),
        # Mid-path ** (the reviewer flagged this — the strip-leading-** branch
        # used to be dead-weight; verify the simple fnmatch path still works)
        ("plugins/security/x/skills/y/SKILL.md", ["plugins/**/SKILL.md"], True),
        ("plugins/a/b/c/d/e/f/SKILL.md", ["plugins/**/SKILL.md"], True),
        ("scripts/x.py", ["plugins/**/SKILL.md"], False),
        # Trailing ** (directory recursion)
        (".github/workflows/foo.yml", [".github/workflows/**"], True),
        (".github/actions/x.yml", [".github/workflows/**"], False),
        # Edge: zero patterns means no match
        ("README.md", [], False),
    ],
)
def test_path_matches_filter(path, patterns, expected):
    assert path_matches_filter(path, patterns) is expected


# =============================================================================
# paths-ignore semantics
# =============================================================================


class TestPathsIgnoreSemantics:
    def test_workflow_fires_when_no_filter(self):
        assert workflow_fires_for(["README.md"], paths=[], paths_ignore=[]) is True

    def test_workflow_fires_when_paths_matches(self):
        assert workflow_fires_for(["scripts/x.py"], paths=["**/*.py"], paths_ignore=[]) is True

    def test_workflow_skips_when_paths_does_not_match(self):
        assert workflow_fires_for(["README.md"], paths=["**/*.py"], paths_ignore=[]) is False

    def test_paths_ignore_skips_when_all_files_match_ignore(self):
        """A `paths-ignore: ['**/*.md']` workflow should NOT fire for a doc-only PR."""
        fires = workflow_fires_for(
            ["docs/a.md", "docs/b.md"],
            paths=[],
            paths_ignore=["**/*.md"],
        )
        assert fires is False

    def test_paths_ignore_fires_when_any_file_not_ignored(self):
        """`paths-ignore: ['**/*.md']` fires if ANY file isn't a markdown."""
        fires = workflow_fires_for(
            ["docs/a.md", "scripts/x.py"],
            paths=[],
            paths_ignore=["**/*.md"],
        )
        assert fires is True


# =============================================================================
# Zero-match / gap detection
# =============================================================================


class TestZeroMatchGapDetection:
    def test_file_matching_no_workflow_appears_nowhere(self):
        """A file pattern that no workflow currently catches should be visible
        as belonging only to the always-on workflows."""
        result = run_routing(["random-experimental-dir/foo.xyz"])
        # The file shouldn't appear in any path-filtered workflow's matched_files
        filtered_workflows = {
            k: v for k, v in result.items() if not k.startswith("_") and isinstance(v, dict)
        }
        for wf_name, entry in filtered_workflows.items():
            assert "random-experimental-dir/foo.xyz" not in entry["matched_files"], (
                f"unexpected match in {wf_name}"
            )

    def test_validate_plugins_in_no_filter_set(self):
        """validate-plugins.yml is the transition baseline — must NOT have a filter."""
        result = run_routing(["README.md"])
        assert "Validate Plugins" in result["_no_filter"]


# =============================================================================
# YAML extraction edge cases
# =============================================================================


class TestYamlExtractionEdgeCases:
    def test_paths_ignore_field_extracted(self, tmp_path):
        """If a workflow uses paths-ignore, our parser should surface it."""
        wf = tmp_path / "x.yml"
        wf.write_text(
            "name: Test Ignore\n"
            "on:\n"
            "  pull_request:\n"
            "    paths-ignore:\n"
            "      - '**/*.md'\n"
            "      - 'docs/**'\n"
            "jobs:\n"
            "  x:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: echo hi\n",
            encoding="utf-8",
        )
        wf_path = wf  # absolute; extract_workflow_metadata uses relative_to(_REPO_ROOT)
        # Can't use the real extractor because it relative_to's against repo root.
        # Just test via temp parse: simulate by reading lines + calling extractor's
        # logic. Easiest: skip relative_to via monkey-patch.
        from importlib import reload
        # Direct functional test via the existing module
        original = _routing._WORKFLOWS_DIR  # noqa: SLF001
        try:
            _routing._WORKFLOWS_DIR = tmp_path  # noqa: SLF001
            meta = _routing.extract_workflow_metadata(wf_path)
        finally:
            _routing._WORKFLOWS_DIR = original  # noqa: SLF001
        assert meta["paths_ignore"] == ["**/*.md", "docs/**"]
        assert meta["uses_paths_ignore"] is True
        assert meta["paths"] == []

    def test_unquoted_glob_in_paths(self, tmp_path):
        """Unquoted globs in YAML must extract without the surrounding quote
        characters (this is the most common shape in practice)."""
        wf = tmp_path / "x.yml"
        wf.write_text(
            "name: Test Unquoted\n"
            "on:\n"
            "  pull_request:\n"
            "    paths:\n"
            "      - '**/*.md'\n"
            '      - "**/*.py"\n'
            "      - scripts/**\n"   # unquoted
            "jobs:\n"
            "  x:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: echo hi\n",
            encoding="utf-8",
        )
        original = _routing._WORKFLOWS_DIR  # noqa: SLF001
        try:
            _routing._WORKFLOWS_DIR = tmp_path  # noqa: SLF001
            meta = _routing.extract_workflow_metadata(wf)
        finally:
            _routing._WORKFLOWS_DIR = original  # noqa: SLF001
        assert meta["paths"] == ["**/*.md", "**/*.py", "scripts/**"]

    def test_workflow_dispatch_only_returns_empty_paths(self, tmp_path):
        """A workflow with no pull_request trigger at all should report no filter."""
        wf = tmp_path / "x.yml"
        wf.write_text(
            "name: Test Dispatch Only\n"
            "on:\n"
            "  workflow_dispatch:\n"
            "jobs:\n"
            "  x:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: echo hi\n",
            encoding="utf-8",
        )
        original = _routing._WORKFLOWS_DIR  # noqa: SLF001
        try:
            _routing._WORKFLOWS_DIR = tmp_path  # noqa: SLF001
            meta = _routing.extract_workflow_metadata(wf)
        finally:
            _routing._WORKFLOWS_DIR = original  # noqa: SLF001
        assert meta["paths"] == []
        assert meta["paths_ignore"] == []
        assert meta["uses_paths_ignore"] is False


# =============================================================================
# Workflow metadata extraction smoke test
# =============================================================================


class TestWorkflowMetadataExtraction:
    def test_extracts_workflow_name(self):
        wf = extract_workflow_metadata(
            _REPO_ROOT / ".github" / "workflows" / "validate-plugins.yml"
        )
        assert wf["name"] == "Validate Plugins"

    def test_extracts_paths_filter(self):
        wf = extract_workflow_metadata(
            _REPO_ROOT / ".github" / "workflows" / "actionlint.yml"
        )
        assert ".github/workflows/**" in wf["paths"]

    def test_workflow_without_filter_returns_empty_paths(self):
        """validate-plugins.yml has no paths: filter (transition baseline)."""
        wf = extract_workflow_metadata(
            _REPO_ROOT / ".github" / "workflows" / "validate-plugins.yml"
        )
        assert wf["paths"] == []
