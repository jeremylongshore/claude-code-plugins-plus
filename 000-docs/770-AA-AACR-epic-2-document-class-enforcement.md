<!-- doc-class: record -->

# Epic 2.5 — Document-class enforcement

- **Authority:** Blueprint 727, Epic 2 bead 2.5 (`claude-hedb.7`)
- **Status:** Implementation evidence; closure follows the focused PR and its independent review.
- **Scope:** Add an explicit lifecycle class to every tracked Markdown document under `000-docs/`,
  then enforce the frozen and generated boundaries in the existing `doc-governance` job.

## Decision

The repository now treats `canonical`, `generated`, `frozen`, and `record` as the complete
machine-readable document-class vocabulary. A class marker must be the first line of every tracked
`000-docs/*.md` file. The marker is descriptive: authority still comes only from
`STANDARDS.md § Canonical documents` and `check-doc-authority.mjs`.

The five superseded `6767-*` standards remain `frozen` and are compared against `origin/main`.
`000-INDEX.md` remains `generated` and is checked by its canonical generator. Current authority
owners named by blueprint 727 §11 are `canonical`; all other tracked Markdown records, including
the archive, are explicitly `record` rather than silently inheriting authority.

## Verification contract

`node scripts/check-doc-classes.mjs` inventories Git-tracked Markdown, rejects missing, malformed,
unknown, or mismatched classes, refuses frozen drift, and runs the generated-index check. Its unit
fixtures cover all classes and fail-closed marker errors. The command runs in the existing
`doc-governance` job, preserving the three required contexts and adding no path filter or fourth
status.

## Rollback and boundaries

Revert the focused implementation merge, restore the prior document bytes, and rerun the live
doc-governance checks. This slice changes only document headers, the class checker/tests, the
existing workflow step, the filing ledger/index, this AAR, and `CHANGELOG.md`. It does not edit
frozen bodies, mirrored content, catalogs, packages, credentials, registries, contributors, Plane,
branch protection, or production.
