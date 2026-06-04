"""Path-routing dry-run tests for the new-track workflow split.

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
# Per-domain routing tests
# =============================================================================


class TestMarkdownRouting:
    def test_pure_markdown_change_fires_lint_markdown(self):
        fired = fires_for(["README.md"])
        assert "Lint Markdown" in fired

    def test_plugin_skill_md_fires_both_markdown_and_skill_codeblocks(self):
        fired = fires_for([
            "plugins/security/penetration-tester/skills/x/SKILL.md",
        ])
        assert "Lint Markdown" in fired
        assert "Lint Skill Code Blocks" in fired

    def test_doc_only_change_does_not_fire_python_or_typescript(self):
        fired = fires_for(["000-docs/some-doc.md"])
        assert "Lint Markdown" in fired
        assert "Lint Python" not in fired
        assert "Lint TypeScript" not in fired
        assert "Lint Shell" not in fired


class TestPythonRouting:
    def test_python_source_fires_lint_python(self):
        fired = fires_for(["scripts/foo.py"])
        assert "Lint Python" in fired

    def test_python_source_does_not_fire_typescript_lint(self):
        fired = fires_for(["scripts/foo.py"])
        assert "Lint TypeScript" not in fired

    def test_pyproject_change_fires_lint_python(self):
        fired = fires_for(["plugins/security/penetration-tester/pyproject.toml"])
        assert "Lint Python" in fired

    def test_requirements_change_fires_lint_python(self):
        fired = fires_for(["plugins/x/requirements.txt"])
        assert "Lint Python" in fired


class TestTypeScriptRouting:
    def test_ts_source_fires_lint_typescript(self):
        fired = fires_for(["packages/cli/src/index.ts"])
        assert "Lint TypeScript" in fired

    def test_js_source_fires_lint_typescript(self):
        fired = fires_for(["scripts/sync-marketplace.cjs"])
        assert "Lint TypeScript" in fired

    def test_tsconfig_change_fires_lint_typescript(self):
        fired = fires_for(["packages/cli/tsconfig.json"])
        assert "Lint TypeScript" in fired

    def test_package_json_fires_lint_typescript(self):
        fired = fires_for(["package.json"])
        assert "Lint TypeScript" in fired


class TestShellRouting:
    def test_shell_script_fires_lint_shell(self):
        fired = fires_for(["scripts/quick-test.sh"])
        assert "Lint Shell" in fired

    def test_shell_script_does_not_fire_python_lint(self):
        fired = fires_for(["scripts/quick-test.sh"])
        assert "Lint Python" not in fired


class TestSkillCodeblocksRouting:
    def test_skill_md_fires_skill_codeblocks(self):
        fired = fires_for([
            "plugins/security/penetration-tester/skills/x/SKILL.md",
        ])
        assert "Lint Skill Code Blocks" in fired

    def test_plugin_readme_fires_skill_codeblocks(self):
        fired = fires_for(["plugins/security/penetration-tester/README.md"])
        assert "Lint Skill Code Blocks" in fired

    def test_top_level_readme_does_not_fire_skill_codeblocks(self):
        """README.md at repo root is NOT a plugin SKILL.md / README.md."""
        fired = fires_for(["README.md"])
        assert "Lint Skill Code Blocks" not in fired


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
    def test_mixed_python_and_typescript_fires_both(self):
        fired = fires_for([
            "scripts/foo.py",
            "packages/cli/src/x.ts",
        ])
        assert "Lint Python" in fired
        assert "Lint TypeScript" in fired

    def test_doc_only_pr_fires_only_markdown_workflows(self):
        """The PR #823 failure mode: doc-only edit should fire ONLY markdown
        workflows. The plugin-structure required check (which still runs
        unfiltered from validate-plugins.yml) is not in this set because
        it has no paths filter."""
        fired = fires_for([
            "plugins/saas-packs/databricks-pack/000-docs/000-INDEX.md",
            "plugins/saas-packs/databricks-pack/000-docs/014-spec.md",
        ])
        assert "Lint Markdown" in fired
        # NO python, TS, shell, actionlint
        assert "Lint Python" not in fired
        assert "Lint TypeScript" not in fired
        assert "Lint Shell" not in fired
        assert "Actionlint" not in fired


# =============================================================================
# Each new workflow has a paths filter
# =============================================================================


class TestEveryNewWorkflowHasPathsFilter:
    """The point of PR 2's split is that each new workflow has a paths filter.
    If a new workflow gains a `paths:` filter only by accident (e.g. fires
    on every PR), this test catches it."""

    EXPECTED_FILTERED_WORKFLOWS = {
        "Lint Markdown",
        "Lint TypeScript",
        "Lint Python",
        "Lint Shell",
        "Lint Skill Code Blocks",
        "Actionlint",
    }

    def test_all_new_workflows_have_paths_filters(self):
        all_wfs = list_all_workflows()
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
            _REPO_ROOT / ".github" / "workflows" / "lint-markdown.yml"
        )
        assert wf["name"] == "Lint Markdown"

    def test_extracts_paths_filter(self):
        wf = extract_workflow_metadata(
            _REPO_ROOT / ".github" / "workflows" / "lint-python.yml"
        )
        assert "**/*.py" in wf["paths"]
        assert "**/pyproject.toml" in wf["paths"]

    def test_workflow_without_filter_returns_empty_paths(self):
        """validate-plugins.yml has no paths: filter (transition baseline)."""
        wf = extract_workflow_metadata(
            _REPO_ROOT / ".github" / "workflows" / "validate-plugins.yml"
        )
        assert wf["paths"] == []
