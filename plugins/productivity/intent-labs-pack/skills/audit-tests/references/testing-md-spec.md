# `tests/TESTING.md` Schema Specification

`tests/TESTING.md` is the per-repo durable state that both `audit-tests` and `implement-tests` read, write, and enforce. It is the single source of truth for classification, policy, installed gates, and audit history in a given repository.

For monorepos: one `TESTING.md` per package, under `<package>/tests/TESTING.md`. The workspace root may have a `TESTING.md` that declares cross-package defaults.

---

## Ownership boundary

| Section | Editable by | Hash-pinned? |
|---|---|---|
| `## Classification (policy)` | Engineer | Yes |
| `## Thresholds (policy, hash-pinned)` | Engineer | Yes |
| `## Installed gates (observational)` | AI | No |
| `## Frameworks (observational)` | AI | No |
| `## Last audit (observational)` | AI | No |
| `## Traceability (observational, updated by audit-tests)` | AI | No |
| `## Hash manifest` | Engineer-initiated | N/A (controls the pin) |

The AI may never modify a policy section. `escape-scan.sh` REFUSES any diff that touches policy lines unless preceded by engineer-initiated `harness-hash.sh --init`.

---

## Canonical structure

```markdown
# Testing Context — <repo-name>
<!-- Managed by audit-tests + implement-tests. Policy sections engineer-owned. -->

## Classification (policy)
Repo type: service | library | cli | frontend | embedded | monorepo-package
Primary language(s): python, typescript
Applicable layers: L1, L2, L3, L4-integration, L6-smoke
Waived layers: L5-a11y (no UI), L7-UAT (product owns)
Compliance overlay: none | HIPAA | SOX | PCI-DSS | SOC2 | GDPR | FedRAMP

## Thresholds (policy, hash-pinned)
coverage.line: 80
coverage.branch: 70
mutation.kill_rate: 70
mutation.per_module:
  payments: 85
  auth: 85
  utils: 70
crap.prod_max: 30
crap.test_max: 15
crap.project_avg: 10
flaky.tolerance: 0/3runs
test.complexity_ceiling: 15
perf.p99_ms: 250   # L5 perf; omit if L5-perf waived
security.owasp_coverage: A  # minimum letter grade

## Installed gates (observational)
L1: husky@9 + lint-staged + commitlint
L2: ruff + mypy + gitleaks (pre-commit)
L3: pytest + coverage.py + mutmut
L4-integration: testcontainers (postgres fixture)
L4-migration: alembic + migration smoke tests
L6-smoke: playwright smoke (12 scenarios)

## Frameworks (observational)
unit: pytest 8.x
coverage: coverage.py 7.x
mutation: mutmut 3.x
e2e: playwright 1.x
bdd: behave 1.2.x

## Last audit (observational)
date: 2026-04-21
grade: B (82/100)
auditor: audit-tests v7.0.0
p0_gaps: 0
p1_gaps: 2
  - missing migration test for 0042_add_user_quota
  - no per-module mutation floor enforced on payments/
p2_gaps: 3

## Traceability (observational, updated by audit-tests)
rtm.total_requirements: 47
rtm.by_moscow:
  must: 22 (22 covered, 0 uncovered)
  should: 14 (11 covered, 3 uncovered)
  could: 8 (4 covered, 4 uncovered)
  wont: 3 (excluded from coverage math)
rtm.orphaned_tests: 2
personas.declared: 4
personas.under_threshold: 1 (premium-customer at 75%)
journeys.declared: 6
journeys.fully_covered: 4
journeys.partial: 2

## Hash manifest
version: 2
last_init: 2026-04-21 by jeremy
protected_files:
  - tests/TESTING.md#policy  # sections above "## Installed gates"
  - features/*.feature
  - .dependency-cruiser.js
  - pyproject.toml#[tool.coverage]
  - pyproject.toml#[tool.mutmut]
  - pyproject.toml#[tool.radon]
```

---

## Reading order for tools

1. `audit-tests` start-of-run:
   - Read `## Classification` → override auto-classification if present.
   - Read `## Thresholds` → pass to `escape-scan.sh` (overrides hardcoded defaults).
   - Read `## Installed gates` → skip presence checks for gates already recorded.
   - Read `## Waived layers` → skip those layer audits entirely.

2. `implement-tests` start-of-run:
   - Read `## Classification` to determine install set.
   - Read `## Thresholds` to know what threshold values to write into installed configs (e.g., `fail_under = {{coverage.line}}`).
   - Read `## Installed gates` to avoid reinstalling what is already present.

3. Both skills, end-of-run:
   - Update `## Installed gates` (implement-tests only) or `## Last audit` + `## Traceability` (audit-tests).
   - Never touch policy sections; never touch the `## Hash manifest`.

---

## Lifecycle

### Creation

First time a repo runs `implement-tests` (or `audit-tests` and finds no `TESTING.md`), the `rtm-scaffolder-agent` writes a skeleton. Policy sections get sensible defaults (coverage.line=80, mutation.kill_rate=70) with an inline comment flagging them for engineer review.

### Mutation

- AI writes to observational sections by Edit tool, never Write (avoids overwrites of engineer edits to policy).
- Engineer edits any policy section manually; after save, runs `bash audit-tests/scripts/harness-hash.sh --init` to re-pin the hash.

### Versioning

Top-of-file version comment:

```markdown
<!-- TESTING.md schema v1 (see audit-tests/references/testing-md-spec.md) -->
```

When the schema changes, bump the version and add a migration note in `implement-tests/references/auto-remediation.md`.

---

## Example: minimal greenfield repo

On first install into a brand-new Python library, `implement-tests` writes:

```markdown
# Testing Context — new-lib
<!-- Managed by audit-tests + implement-tests. Policy sections engineer-owned. -->

## Classification (policy)
Repo type: library
Primary language(s): python
Applicable layers: L1, L2, L3
Waived layers: L4, L5, L6, L7 (library — no service, no UI)
Compliance overlay: none

## Thresholds (policy, hash-pinned)
coverage.line: 80
coverage.branch: 70
mutation.kill_rate: 70
crap.prod_max: 30
crap.test_max: 15
crap.project_avg: 10
flaky.tolerance: 0/3runs
test.complexity_ceiling: 15

## Installed gates (observational)
L1: pre-commit (ruff, mypy, gitleaks)
L2: ruff 0.5.x + mypy 1.10
L3: pytest 8 + coverage.py 7 + mutmut 3 + radon 6 + hypothesis 6

## Frameworks (observational)
unit: pytest 8.x
coverage: coverage.py 7.x
mutation: mutmut 3.x

## Last audit (observational)
date: never
grade: pending first audit

## Hash manifest
version: 1
last_init: 2026-04-21 by <engineer>
protected_files:
  - tests/TESTING.md#policy
  - pyproject.toml#[tool.coverage]
  - pyproject.toml#[tool.mutmut]
```

---

## What NOT to put in `TESTING.md`

- Transient audit output → goes in `TEST_AUDIT.md` (top of repo, gitignored or short-lived).
- Per-test failure traces → framework outputs, not policy.
- CI platform specifics → lives in `.github/workflows/*` etc., summarized here by gate name only.
- Stack traces, logs, metrics history → that belongs in observability tooling.

`TESTING.md` is the *policy and installed-system map* — it should fit on one screen once populated.
