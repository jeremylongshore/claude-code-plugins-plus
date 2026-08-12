# 723-RA-AUDT — Version Drift Report (Mission 01)

**Captured:** 2026-08-11 @ `4358a65a3`

## The invariant gap

The repo has **five version surfaces** (catalog entry · `plugin.json` · derived
`marketplace.json` · SKILL.md frontmatter · npm package versions) and a purpose-built checker —
`scripts/reconstruct-versions.mjs --check` — that is wired into **no workflow**. Zero enforced
invariant connects the surfaces today.

## Live drift measurement (first recorded run of `--check`)

- **1 plugin disagrees:** `plugins/productivity/intent-labs-pack` — catalog `0.1.0` vs
  `skills/audit-tests/SKILL.md` `7.2.0` and `skills/validate-skillmd/SKILL.md` `5.0.1`.
- **1 dir unchecked:** `plugins/skill-enhancers/axiom` (no `plugin.json` — vendored
  sub-marketplace shape).
- Corpus otherwise agrees across surfaces.

## Kernel / tooling pins (governance-tracked, not drift to "fix" here)

- `@intentsolutions/core` pinned exactly `0.9.0`; published `0.10.0` (2026-07-09). The ≤7-day
  staleness bound has been breached since ~2026-07-16 — **known, documented, advisory-only**.
  The bump is a deliberate lockstep change with `@intentsolutions/jrig-cli` (pinned `0.1.2`),
  never a side effect (see CLAUDE.md § Validation & the kernel SSoT).

## Freshie run-stamp inconsistency (confirmed)

`freshie/grade-histogram.json` carries `run_id: 10` (total 3,678) while only the `run-delta-9`
tag is committed and the `dolt_commit` stamp is absent. The next `dolt-sync.py` run re-stamps —
FIX bead, no manual edit.

## Proposed FIX beads (approval-gated)

1. Wire `reconstruct-versions.mjs --check` as an **advisory** CI job (never straight into the
   required set — see CI gate architecture rules).
2. Align `intent-labs-pack` versions deliberately (owner decides which surface is truth).
3. Freshie re-stamp via the normal sync path.
