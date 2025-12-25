# Branch and Release Flow (Operator Discipline)

## Goals

- Keep `main` clean and always mergeable.
- Make work reviewable via small, scoped feature branches.
- Require CI to be green before merge.

## Branch Discipline

- Default branch: `main`
- Work branches: `feature/<scope>` (example: `feature/phase-0-repo-stabilization`)
- Never commit directly to `main`.
- Keep PRs tightly scoped to the phase/epic.

## Merge Discipline

- CI must be green before merge (see `.github/workflows/`).
- Prefer **squash merge** for feature branches.
- Squash commit message format (recommended):
  - `phase0(docs): <summary>`
  - `phase1(<area>): <summary>`

## Release / Deploy Discipline (facts + guardrails)

- Website build/deploy lives under `marketplace/` and is driven by CI workflows.
- Workspace builds/tests run under root `pnpm` scripts.
- Do not change deploy logic in Phase 0; record needed changes in the Phase 1 punchlist.

## “Landing the Plane” Checklist (per `AGENTS.md`)

Before ending a work session:
1) Run feasible local verification (build/test/lint where possible)
2) Update Beads issues (close/advance)
3) `git pull --rebase`
4) `bd sync`
5) `git push`

