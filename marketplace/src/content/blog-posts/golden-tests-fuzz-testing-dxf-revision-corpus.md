---
title: "Golden Tests, Fuzz Testing, and a Nasty Fixture Taxonomy for DXF Revisions"
description: "Building a test corpus with clean/nasty fixture taxonomy, golden file regression tests, and fuzz testing for a DXF comparison engine."
date: "2026-02-27"
tags: ["testing", "python", "architecture", "ai-agents", "cad"]
featured: false
---
Yesterday I shipped a [deterministic DXF comparison engine](/blog/deterministic-dxf-comparison-engine-one-day-build/) — canonical models, alignment ladders, confidence scoring, the works. Four PRs, 814 tests, all green.

Today's question: does it actually work on drawings that aren't contrived?

## The Problem with Unit Tests Alone

Unit tests prove individual functions behave correctly. They don't prove the pipeline survives a revision where the drafter only updated the left half of the sheet, or where the master drawing is in inches and the revision is in millimeters.

Production DXF files are hostile. Blocks with changed attributes. Rotated + shifted coordinate systems. External references that look like real entities. You can't cover these with `assertEqual(a, b)`.

## Clean vs Nasty: A Fixture Taxonomy

I split the test corpus into two directories with very different purposes.

**Clean fixtures** are the happy path. A 3x2 column grid where one column moved. A wall that got thicker. An embedded detail that was added. These prove the basic pipeline works end-to-end and make good regression anchors.

**Nasty fixtures** are the five categories that will actually break your code:

- **partial_revision** — revision only covers the left half of the sheet. Right-side entities are completely absent. Does your differ panic or report them as deletions?
- **unit_mismatch** — master in inches, revision in millimeters. A 25.4x scale factor that turns every coordinate comparison into garbage if you don't detect it.
- **rotation_shift** — revision rotated 12 degrees and shifted, plus one genuine change buried in the noise. Does your alignment ladder find the real delta?
- **block_attrib_changes** — door blocks where ROOM and SIZE attributes changed but the geometry is identical. Attribute-only diffs are easy to miss.
- **xrefs** — external reference blocks that shouldn't confuse entity matching. XREFs aren't real entities in the current drawing.

Three more fixtures are seeded from real-world ezdxf examples: BricsCAD nested blocks, 18 uncommon entity types (DIMENSION, SPLINE, MESH, 3DSOLID), and a column layout with MTEXT modifications.

## Golden Tests: Regression Detection on Autopilot

Every fixture pair gets an `expected.json` — the committed ground truth for what the comparison engine should produce. The test harness auto-discovers all fixtures and compares output against golden files:

```python
import pytest
from pathlib import Path

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "revision"

def discover_fixture_pairs():
    pairs = []
    for category in sorted(FIXTURE_ROOT.iterdir()):
        if not category.is_dir():
            continue
        master = category / "master.dxf"
        revision = category / "revision.dxf"
        expected = category / "expected.json"
        if master.exists() and revision.exists() and expected.exists():
            pairs.append(pytest.param(
                master, revision, expected,
                id=category.name,
            ))
    return pairs

@pytest.mark.parametrize("master,revision,expected", discover_fixture_pairs())
def test_revision_matches_golden(master, revision, expected, compare_engine):
    result = compare_engine.compare(master, revision)
    golden = json.loads(expected.read_text())
    assert result.to_dict() == golden
```

When behavior changes intentionally, `UPDATE_GOLDENS=1 pytest` regenerates all golden files. You review the diff in your PR. This is the key insight — golden tests turn "did the output change?" into a git diff you can review with your eyes.

## Fuzz Tests: Proving the Pipeline Doesn't Crash

Golden tests catch regressions. They don't prove the engine handles inputs you haven't thought of yet. That's what fuzz tests are for.

Seven property tests, 20 iterations each, generating random drawings and applying transformations:

```python
@given(drawing=random_dxf_drawing(max_entities=50))
@settings(max_examples=20)
def test_translation_invariance(drawing, compare_engine):
    """Translating a drawing should produce zero diffs."""
    shifted = translate(drawing, dx=random.uniform(-1000, 1000),
                                  dy=random.uniform(-1000, 1000))
    result = compare_engine.compare(drawing, shifted)
    assert result.changes == []

@given(drawing=random_dxf_drawing(max_entities=50))
@settings(max_examples=20)
def test_deletion_detected(drawing, compare_engine):
    """Deleting a random entity should produce exactly one deletion."""
    modified, deleted_id = delete_random_entity(drawing)
    result = compare_engine.compare(drawing, modified)
    assert len(result.deletions) == 1
```

Translation invariance, rotation invariance, noise tolerance, deletion detection, addition detection, attribute mutation, combined transforms. If any of these crash or produce wrong results on random input, Hypothesis will shrink the failure to the minimal reproducing case.

## The CLI: Plumbing That Matters Later

Also scaffolded the `cad-revision` CLI with six subcommands: `diff`, `align`, `dry-run`, `apply`, `bundle`, `explain`. Argparse with `--json` output and `--verbose` logging. Entry point registered in `pyproject.toml`. 47 tests covering argument parsing, output formats, and error handling.

The CLI is plumbing right now. It becomes the user interface once the engine stabilizes.

## The Numbers

- 936 total tests (up from 814 yesterday)
- 8 clean fixtures, 8 nasty fixtures
- 7 fuzz test properties x 20 iterations = 140 randomized scenarios per run
- 47 CLI tests
- Full E2E smoke test: compare, dry-run, approve, apply, export bundle

Testing infrastructure IS the feature. The golden harness catches regressions automatically. The fuzz tests prove the pipeline doesn't crash on garbage. The nasty fixtures cover the edge cases that will show up the first time someone feeds in a drawing from a different CAD vendor with different unit conventions and a partially-updated revision.

---

**Related Posts:**

- [Building a Deterministic DXF Comparison Engine in One Day](/blog/deterministic-dxf-comparison-engine-one-day-build/)
- [The Silent Killer: Bare Catch Blocks Hide Failures](/blog/silent-killer-bare-catch-blocks-hide-failures/)
- [Python Class Identity Mismatch: A CI Debugging Guide](/blog/python-class-identity-mismatch-ci-debugging-guide/)
