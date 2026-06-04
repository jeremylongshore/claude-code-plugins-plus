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
    ],
)
def test_path_matches_filter(path, patterns, expected):
    assert path_matches_filter(path, patterns) is expected


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
