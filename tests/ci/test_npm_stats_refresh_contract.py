"""Regression checks for the daily npm-stats publication contract.

The generator owns two public surfaces: ``npm-stats.json`` and the README
``NPM-STATS`` block. A 2026-09-02 run updated the JSON but caught a missing
Prettier import and silently skipped the README, producing a green workflow and
a self-contradictory PR. These checks pin dependency setup, fail-closed error
handling, and prepare-before-write ordering.
"""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "update-npm-stats.yml"
GENERATOR = REPO_ROOT / "scripts" / "fetch-npm-stats.mjs"


def test_workflow_installs_generator_dependencies_before_fetching() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    corepack = workflow.index("run: corepack enable")
    install = workflow.index(
        'run: pnpm install --frozen-lockfile --filter "claude-code-plugins-monorepo" --ignore-scripts'
    )
    fetch = workflow.index("run: node scripts/fetch-npm-stats.mjs")

    assert corepack < install < fetch


def test_readme_formatting_is_required_and_precedes_artifact_writes() -> None:
    generator = GENERATOR.read_text(encoding="utf-8")

    assert "import prettier from 'prettier';" in generator
    assert "README update skipped" not in generator

    format_readme = generator.index("const readmeOutput = await formatter.format")
    write_json = generator.index("writeFileSync(OUT_JSON, jsonOutput)")
    write_readme = generator.index("writeFileSync(README, updatedReadme)")

    assert format_readme < write_json < write_readme
