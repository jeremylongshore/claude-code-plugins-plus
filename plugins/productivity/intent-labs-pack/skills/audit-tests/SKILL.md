---
name: audit-tests
description: "Diagnostic-only test suite auditor. Classifies repo type, maps against\
  \ 7-layer testing taxonomy (git hooks \u2192 static \u2192 unit \u2192 integration\
  \ \u2192 system \u2192 E2E \u2192 acceptance), runs deterministic quality gates\
  \ (coverage, mutation, CRAP, architecture, escape-scan), builds RTM / personas /\
  \ journeys traceability, produces TEST_AUDIT.md, updates tests/TESTING.md, and mandatorily\
  \ hands off to implement-tests when gaps are found. Use when auditing test quality,\
  \ finding test gaps, or running the full 7-layer sweep. Trigger with \"audit tests\"\
  , \"find gaps\", \"test audit\", \"check test quality\", \"full sweep\", \"7-layer\
  \ audit\", \"rtm check\"."
version: 7.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
model: inherit
allowed-tools: Read, Glob, Grep, Bash(find:*), Bash(git:*), Bash(gh:*), Bash(ls:*),
  Bash(pnpm:*), Bash(npx:*), Bash(pytest:*), Bash(go:*), Bash(cargo:*), Bash(bash:*),
  Bash(sha256sum:*), Bash(python:*), Bash(python3:*), Bash(radon:*), Bash(gocyclo:*),
  Bash(depcruise:*), Bash(gherkin-lint:*), Task, AskUserQuestion, Skill
tags:

- testing
- audit
- quality-gates
- taxonomy
- containment
- rtm
- moscow
compatibility: Designed for Claude Code
---

# audit-tests — Diagnostic Test Auditor (7-Layer + RTM)

**Invocation**: "audit tests" · "find gaps" · "full sweep" · "7-layer audit" · "rtm check" · "test quality".

> **Enforcement harness**: this skill delegates all deterministic checks (hash-pin, escape-scan, CRAP, architecture, bias, Gherkin lint) to the in-repo installation of [`@intentsolutions/audit-harness`](https://www.npmjs.com/package/@intentsolutions/audit-harness). Node repos install via `pnpm add -D @intentsolutions/audit-harness`; other languages vendor via the package's `install.sh`. **Never reference `~/.claude/...` paths from a target repo's hooks or CI** — the enforcement must travel with the code.

Read-only diagnostic skill. Classifies the repo, maps applicable layers from the 7-layer testing taxonomy, runs deterministic gates, builds requirements traceability (RTM / personas / journeys), writes `TEST_AUDIT.md` + updates `tests/TESTING.md`, and **mandatorily hands off** to `implement-tests` when P0/P1 gaps exist.

No filesystem mutations other than `TEST_AUDIT.md` (transient) and the observational sections of `tests/TESTING.md`, `tests/RTM.md`, `tests/PERSONAS.md`, `tests/JOURNEYS.md`.

## Overview

Diagnostic-only test suite auditor for any Intent Solutions (or compatible) repo.
Classifies the repository, maps the 7-layer testing taxonomy, runs deterministic
gates via in-repo `@intentsolutions/audit-harness`, builds RTM/personas/journeys
traceability, and writes `TEST_AUDIT.md` plus observational sections of
`tests/TESTING.md`. When P0/P1 gaps exist it **hands off** to `implement-tests`
instead of implementing tests itself.

## Prerequisites

- A git working tree for the target repository
- Ability to run `Read`/`Glob`/`Grep`/`Bash` against that tree
- For deterministic gates: in-repo `audit-harness` (or install path documented
  for the language) — **never** wire target CI/hooks to `~/.claude/...`

## You are the engineer

Deterministic tools do the grading. The engineer owns the walls (`features/*.feature`, coverage thresholds, architecture rules, `TESTING.md` policy sections, `RTM.md` MoSCoW tags). The AI operates inside them and never grades itself — every gate is a tool that returns exit 0.

## Ownership (audit-tests may READ; never modify)

| Artifact | Owner |
|---|---|
| `features/*.feature` | Engineer — hash-pinned |
| Policy sections of `tests/TESTING.md` | Engineer — hash-pinned |
| Coverage / mutation / CRAP thresholds | Engineer (policy) |
| `.dependency-cruiser.js`, `.importlinter`, `deptrac.yaml`, ArchUnit rules | Engineer — hash-pinned |
| `RTM.md` MoSCoW tag overrides | Engineer — hash-pinned; AI never lowers a MUST |
| Test code, step glue, fixtures | AI — edits allowed (in implement-tests only) |

## The 7-layer taxonomy (canonical)

| Layer | Name | Reference |
|---|---|---|
| L1 | Git hooks & CI enforcement | `shared-refs/hooks-and-ci.md` |
| L2 | Static analysis & linting | `shared-refs/linters-formatters-types.md` + `shared-refs/security-testing.md` |
| L3 | Unit & function (walls 2–7 live here) | `shared-refs/frameworks.md`, `shared-refs/crap-and-complexity.md`, `shared-refs/architecture-constraints.md`, `shared-refs/property-and-fuzz.md`, `test-quality-deep-audit.md` |
| L4 | Integration & regression (contract, migration, fakes, IaC) | `shared-refs/integration-and-infra.md`, `shared-refs/specialized-testing.md` |
| L5 | System quality (perf, sec, a11y, compat, chaos) | `shared-refs/security-testing.md`, `shared-refs/specialized-testing.md`, `shared-refs/property-and-fuzz.md` § Chaos |
| L6 | E2E / BDD / Gherkin (smoke, visual) | `shared-refs/e2e-testing.md`, `shared-refs/acceptance-tests-gherkin.md` |
| L7 | Acceptance & business validation (UAT) | `shared-refs/acceptance-tests-gherkin.md` |

Full definitions and gap-fill rationale: `{baseDir}/references/taxonomy.md`.
Classification → applicable layers: `{baseDir}/references/layer-applicability.md`.

**Walls live inside layers.** Wall 1 (Acceptance) = L7 spec + L6 glue. Walls 2–7 = L3. See `taxonomy.md` § "Walls inside layers".

## Instructions

### Step 0.5 — Harness freshness check (automatic, ≤ 500ms, cache 24h)

Run this early so drift surfaces without remembering to invoke `/sync-testing-harness`:

```bash

CACHE=~/.cache/audit-harness/freshness-check
mkdir -p "$(dirname "$CACHE")"

# Skip if checked in last 24h

if [[ -f "$CACHE" ]] && [[ $(($(date +%s) - $(date -r "$CACHE" +%s))) -lt 86400 ]]; then
  cat "$CACHE"
else
  latest=$(curl -fsS --max-time 3 https://registry.npmjs.org/@intentsolutions/audit-harness/latest 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin)["version"])' 2>/dev/null || echo "unknown")
  installed=$(pnpm list @intentsolutions/audit-harness --depth=0 --json 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d[0].get("devDependencies",{}).get("@intentsolutions/audit-harness",{}).get("version","none"))' 2>/dev/null || echo "none")
  if [[ "$latest" != "unknown" && "$latest" != "$installed" && "$installed" != "none" ]]; then
    msg="⚠ audit-harness drift: installed=$installed → latest=$latest. Run /sync-testing-harness or: pnpm up @intentsolutions/audit-harness"
  else
    msg="✓ audit-harness: $installed (latest: $latest)"
  fi
  echo "$msg" | tee "$CACHE"
fi

```

- Cache hit (< 24h old) → instant, no network
- Network failure → silently skipped (offline-safe)
- Drift detected → surfaced in `TEST_AUDIT.md` under `## Freshness`
- **Not blocking** — audit continues regardless

### Step 1 — Read context

1. Check for `tests/TESTING.md`. If absent → proceed to discovery. If present → read `## Classification`, `## Thresholds`, `## Waived layers`. **Engineer policy wins.**
2. Verify the target repo has `@intentsolutions/audit-harness` installed (Node: `package.json` devDep; other langs: `.audit-harness/` directory exists). If absent, add to the handoff payload as L0 install. **Hooks and CI reference the in-repo harness, never `~/.claude/` paths.**
3. Verify hash manifest via `pnpm exec audit-harness verify` (Node) or `scripts/audit-harness verify` (vendored). Interpret exit code:
   - **0** (OK) — pinned hashes match; continue.
   - **2** (`HARNESS_TAMPERED`) — pinned artifact changed; halt the pipeline; flag in `TEST_AUDIT.md` and do not proceed.
   - **3** (no manifest) — fresh repo or never initialized; continue. Log "no hash manifest — fresh repo" in the report. This is NOT a halt condition.
4. Check current branch. On `main` / `develop` / protected branches, any handoff at Step 8 will prompt via `AskUserQuestion`. On `feat/*` branches, handoff runs autonomously.

### Step 2 — Classify

**Deterministic floor first (the harness brain).** Run `pnpm exec audit-harness classify` (Node) / `scripts/audit-harness classify` (vendored) / `audit-harness classify` to emit the read-only `audit-profile/v1` value — the UNION of detected classifications (service / api / library / cli / frontend / embedded / monorepo + skill / agent / hook / mcp / plugin / marketplace / action), the resolved gate set (a projection of `registry.v1.json`, recorded by `registry_hash`), and an explicit `unresolved[]`.

Then dispatch `test-discovery-agent` (via Task tool) **only to refine the `unresolved[]` residue** (ambiguous/novel repos) — it proposes classification patches a human pins in `.audit-harness.yml`/`TESTING.md`; it **never overrides the deterministic classification value** (keeps CI reproducible). Matrix + signals: `{baseDir}/references/layer-applicability.md` (itself generated from the registry datum via `audit-harness gen-layer-applicability`).

Monorepo: the profile carries `per-package-classify`; classify each package independently and run the full pipeline per-package.

### Step 3 — Map applicable layers

The applicable gates are **already resolved in the `audit-profile/v1`** from Step 2 (dimension + applicability + enforcement per gate). Dispatch `taxonomy-mapper-agent` to map presence/absence/configured/enforced **on top of the profile's gate set** + the `TESTING.md` compliance overlay.

Output: gap list tagged P0/P1/P2 per `layer-applicability.md` severity symbols.

### Step 4 — Run deterministic quality gates

**Run the harness gate-runners** — each is read-only and emits `gate-result/v1` Evidence Bundle rows the `quality-gate-runner-agent` consumes:

| Verb | Dimension | Notes |
|---|---|---|
| `audit-harness conform` | conformance | SKILL.md / .mcp.json / plugin / agent vs bundled content-addressed schemas |
| `audit-harness audit [--deep]` | testing-depth | crap-score + per-layer presence (does NOT execute the repo's suite) |
| `audit-harness scan` | security / hygiene / skill-quality | shells out to gitleaks/osv/semgrep/syft/markdownlint/lychee; consumes j-rig verdict |
| `audit-harness currency` | upstream currency | advisory report only (no exit authority) |

New gates ship `enforcement: advisory`; blocking is engineer-pinned in `TESTING.md`, FP-rate-gated (`audit-harness fp-rate`, ≤ 5% bar — see `docs/gate-promotion.md`). Then dispatch `quality-gate-runner-agent` for the L3 measurement tools and capture exit-code + report:

| Gate | Command |
|---|---|
| Coverage | `pytest --cov --cov-fail-under=$(TESTING.md coverage.line)` or framework equivalent |
| Mutation | `mutmut run` / `npx stryker run` / `cargo mutants run` |
| CRAP & complexity | `python3 {baseDir}/scripts/crap-score.py --target both --out reports/crap/` |
| Architecture | `bash {baseDir}/scripts/arch-check.sh` |
| Bias count | `bash {baseDir}/scripts/bias-count.sh` |
| Gherkin lint | `bash {baseDir}/scripts/gherkin-lint.sh` |

Gate failure on prod CRAP > 30, test CRAP > 15, project average > 10, architecture violation > 0, or coverage below policy floor → halt the pipeline; record in `TEST_AUDIT.md`.

### Step 5 — Meta-audit (RTM / personas / journeys)

Dispatch three specialists in parallel (Task tool):

- `rtm-builder-agent` — rebuild `tests/RTM.md` from Gherkin scenarios, ADRs, product docs, engineer-declared REQs, commit tags. Apply MoSCoW precedence (explicit tag → source default → engineer override → SHOULD fallback). Preserve engineer overrides. See `{baseDir}/references/rtm-personas-journeys.md`.
- `persona-coverage-agent` — rebuild `tests/PERSONAS.md`; compute per-persona flow coverage; flag personas below threshold.
- `journey-mapper-agent` — rebuild `tests/JOURNEYS.md`; per-step layer mapping; flag untested steps.

Classify findings:

| Finding | Severity |
|---|---|
| Uncovered MUST requirement | P0 (blocks audit — triggers handoff) |
| Uncovered SHOULD requirement | P1 (advisory; regulated overlay escalates to P0) |
| Uncovered COULD requirement | P2 (logged only) |
| WON'T requirement | excluded from coverage math |
| Orphaned test (no linked REQ) | P1 advisory (regulated: P1; normal: P1) |
| Persona below flow-coverage threshold | P1 advisory |
| Journey step untested (step linked to a MUST REQ) | P0; (linked to SHOULD) P1; (COULD) P2 |

### Step 6 — Escape-scan on any pending diff

Dispatch `escape-detection-agent`:

```bash

bash {baseDir}/scripts/escape-scan.sh --staged    # reads policy floors from tests/TESTING.md

```

Exit grammar: 0 clean · 1 CHALLENGE · 2 REFUSE. Any REFUSE halts the audit with the specific pattern recorded in `TEST_AUDIT.md`.

### Step 7 — Write reports

1. **`TEST_AUDIT.md`** at repo root (transient; short-lived):
   - Grade (letter + numeric)
   - Classification confirmed + applicable layers + waived layers
   - Per-layer presence / config / enforcement table
   - P0/P1/P2 gap list
   - RTM summary (by MoSCoW tier)
   - Persona + journey coverage summary
   - Escape-scan result
2. **`tests/TESTING.md`** — update observational sections only (`## Installed gates`, `## Frameworks`, `## Last audit`, `## Traceability`) via `Edit` tool, never `Write`. Policy sections untouched. Schema: `{baseDir}/references/testing-md-spec.md`.

### Step 8 — Mandatory handoff to implement-tests

```

if any(P0 gaps) OR any(P1 gaps):
    payload = {
        "classification": {...},
        "tests_md_path": "tests/TESTING.md",
        "p0_gaps": [...],
        "p1_gaps": [...],
        "rtm_gaps": [...],         # uncovered MUSTs
        "persona_gaps": [...],
        "journey_gaps": [...],
        "install_order": [L1, L2, L3, ...]   # from scaffold-architect-agent
    }
    if branch in {main, develop, protected}:
        confirm = AskUserQuestion("P0/P1 gaps found. Run implement-tests now?")
        if not confirm: exit with report
    Skill("implement-tests", args=payload)
else:
    print "✓ No P0/P1 gaps. Audit clean."

```

Handoff pattern mirrors `repo-sweep → gist-auditor` — no silent escalation, but autonomous on feature branches per global git policy.

## Escape-detection response grammar

| Severity | Exit | Action |
|---|---|---|
| FLAG | 0 | logged; pipeline continues |
| CHALLENGE | 1 | halts until engineer-approved comment |
| REFUSE | 2 | pipeline halted |

Patterns that REFUSE (non-exhaustive — full list in `{baseDir}/shared-refs/security-testing.md` and the script itself):

| Pattern | Why |
|---|---|
| Coverage threshold lowered below `TESTING.md` floor | Policy violation |
| `.feature` file mutated | Wall 1, hash-pinned |
| `MUST` → weaker tier in `RTM.md` | Requirements downgrade |
| Architecture-rule config edited | Wall 7, hash-pinned |
| Wholesale test-file deletion | Suite weakening |
| Mutation bypass (`pragma: no mutate`, `// Stryker disable`) | Wall 4 evasion (CHALLENGE) |

Deep reference for the full grammar, rationale, and wall derivations: `{baseDir}/references/philosophy.md`.

## Specialist agents (Phase 1 — single-file)

Each lives at `~/.claude/agents/{agent-name}.md`. Audit-tests dispatches via Task tool.

| Agent | Responsibility |
|---|---|
| `test-discovery-agent` | Walk repo; detect frameworks + stack; classify repo type; map source↔test files |
| `taxonomy-mapper-agent` | Presence / config / enforcement per-layer map given classification |
| `quality-gate-runner-agent` | Execute coverage / mutation / CRAP / arch / bias / gherkin scripts; parse outputs |
| `escape-detection-agent` | Run `escape-scan.sh` + `harness-hash.sh --verify`; report REFUSE / CHALLENGE / FLAG |
| `rtm-builder-agent` | Build/update `RTM.md`; apply MoSCoW precedence; flag orphans + uncovered |
| `persona-coverage-agent` | Compute per-persona flow coverage in `PERSONAS.md` |
| `journey-mapper-agent` | Map journey steps to layer-tests in `JOURNEYS.md` |

**Phase 2** (deferred): each agent may be upgraded to a full skill bundle with its own references/ scripts/ evals/ — see the implementation plan's "Phase 2 Roadmap".

## Discovery and pre-flight

Full discovery logic (config-file scan, language detection, package-manager detection, monorepo detection): `{baseDir}/references/discovery-preflight.md`.

## Quality gate deep-dives

Catalog of every gate tool across 10 sweep categories (aligned to 7-layer taxonomy): `{baseDir}/references/quality-gates-sweep.md`.

Per-layer test-quality bias rules, OWASP mapping, mutation interpretation: `{baseDir}/references/test-quality-deep-audit.md`.

GitHub-scoped audit (CI health, branch protection, coverage-threshold enforcement): `{baseDir}/references/github-audit.md`.

## Output

### Clean audit

```

AUDIT COMPLETE — {repo-name}
Grade:            A (92/100)
Classification:   service
Applicable:       L1, L2, L3, L4-integ, L4-contract, L5-sec, L6-smoke
Waived:           L5-a11y (no UI), L7-UAT
P0 gaps:          0
P1 gaps:          0
RTM:              22 MUST / all covered · 14 SHOULD / 14 covered
Escape-scan:      clean
Report:           TEST_AUDIT.md
TESTING.md:       updated (observational sections)
Handoff:          none needed

```

### Gaps found (feat branch — autonomous)

```

AUDIT COMPLETE — {repo-name}
Grade:            C (68/100)
P0 gaps:          2 (L3 coverage below 80; REQ-002 MUST uncovered)
P1 gaps:          5
Handoff →         implement-tests (autonomous; feat branch)

```

### Gaps found (main branch — confirmation prompt)

```

AUDIT COMPLETE — {repo-name}
Grade:            C (68/100)
P0 gaps:          2
P1 gaps:          5
Branch:           main (protected) — prompting for handoff confirmation...

```

## Examples

**Example 1 — Fresh Python library, no tests yet.**
Run `audit tests` → `test-discovery-agent` classifies as `library`, no `TESTING.md` present → `taxonomy-mapper-agent` reports L1, L2, L3 all absent (P0), L4–L7 waived per library applicability → `rtm-scaffolder` schedules skeleton creation → handoff payload: `install_order: [L1, L2, L3]` → autonomous handoff fires (feat branch) → `implement-tests` scaffolds pytest + coverage + mutmut + ruff + pre-commit + starter tests.

**Example 2 — Mature service, previously audited.**
Run `full sweep`. All layers report `installed`; coverage 82% (above 80 floor); mutation kill rate 74% (above 70 floor); CRAP max 22 (below 30). Grade: A (92/100). `TESTING.md#Last audit` updated with today's date. No handoff.

**Example 3 — Monorepo with three packages.**
Run `audit tests`. `test-discovery-agent` returns `monorepo: true, packages: [a, b, c]`. Each package classified independently (`packages/a` = service, `packages/b` = library, `packages/c` = cli). Each gets a per-package `TESTING.md`. Aggregate `TEST_AUDIT.md` at repo root has three sections. Handoff payload includes per-package `install_order` arrays.

**Example 4 — PR lowers coverage threshold to bypass gate.**
A PR proposes `[tool.coverage.report] fail_under = 60` in `pyproject.toml`. `TESTING.md#Thresholds` has `coverage.line: 80`. `escape-detection-agent` runs `escape-scan.sh --staged`. The script reads floor 80 from `TESTING.md`, sees fail_under dropped to 60, emits `[REFUSE] coverage fail_under lowered below policy floor (80)`, exits 2. Audit halts. No `TEST_AUDIT.md` produced. No handoff. Engineer must revert the threshold edit or run `harness-hash.sh --init` to legitimize a policy change.

**Example 5 — HIPAA-compliant service with uncovered SHOULD.**
Repo has `Compliance overlay: HIPAA` in `TESTING.md`. `RTM.md` has one uncovered `SHOULD` (error-message retry logic). Normally P1 advisory, but the regulated overlay promotes it to P0. Handoff fires with `p0_gaps: [{layer: L3, gap: REQ-034 retry logic uncovered (SHOULD, HIPAA overlay)}]`. On `main` branch → `AskUserQuestion` prompts; engineer approves; `implement-tests` proceeds.

## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| `rg: error parsing flag -E: grep config error: unknown encoding` | Shell has `grep` aliased to `rg` (ripgrep); flag grammar differs. | Use `/usr/bin/grep` explicitly, or `command grep`, or call the native `Grep` tool. All detection examples in this SKILL assume GNU `grep`. |
| `error: unexpected argument '-m' found` (from `find`) | Shell has `find` aliased to `fd`; flag grammar differs. | Use `/usr/bin/find` explicitly, or `command find`, or call the native `Glob` tool. All detection examples assume GNU `find`. |
| `gh label create` appears to succeed but label already existed | `gh label create` is a silent no-op without `--force`. | Use `gh label create <name> --description "..." --color <hex> --force` when creating labels idempotently in automation. |
| `HARNESS_TAMPERED` at Step 1 | A hash-pinned file was modified since last `--init`. | Review the diff; if legitimate, run `pnpm exec audit-harness init` (Node) / `scripts/audit-harness init` (vendored) to re-pin; if unexpected, investigate the diff before re-init. |
| `escape-scan` REFUSES on a legitimate threshold change | Thresholds are policy — lowering triggers REFUSE. | Engineer edits `tests/TESTING.md#Thresholds`, then runs `harness-hash.sh --init`. AI cannot do this step. |
| `test-discovery-agent` returns `repo_type: unknown` | No recognizable manifest (package.json, pyproject.toml, etc.). | Add the correct manifest for your language; or set `Repo type:` manually in `tests/TESTING.md#Classification`. |
| Handoff does not fire on feat branch | Branch name does not match `feat/*` pattern, or no P0/P1 gaps found. | Check branch name; if gaps exist and handoff still does not fire, check that `Skill` tool is in the allowed-tools frontmatter. |
| `AskUserQuestion` prompt loops on main | Engineer keeps declining handoff — expected behavior. | Decline is logged; `TEST_AUDIT.md` still produced. To force handoff, merge to a feat branch first. |
| `rtm-builder-agent` keeps re-promoting a MUST | Engineer override was not preserved because `RTM.md` was rewritten (Write instead of Edit). | Ensure the agent uses `Edit` tool on RTM.md; engineer override is detected by row-level MoSCoW value diff. |
| Missing `coverage.py` / `mutmut` / other tool | Measurement tool not installed. | Handoff to `implement-tests` with the specific layer; it installs the measurement tool per the L3 playbook. |
| Monorepo produces only root-level audit | `pnpm-workspace.yaml` / `turbo.json` / `nx.json` not present or unrecognized. | Confirm workspace config is at repo root; or manually declare per-package `TESTING.md` files. |

## Edge cases

- **Missing framework**: record gap; skip the measurement; emit `install_order: [framework]` in handoff.
- **Docker unavailable** for integration tests: skip L4 integration measurement; still report the gap as "unmeasured — Docker missing".
- **Hash mismatch**: `HARNESS_TAMPERED` — halt before any other work; do not write `TEST_AUDIT.md`.
- **Engineer-declared waiver**: any layer listed in `TESTING.md#Waived layers` is skipped silently; appears in report under "Waived (per engineer policy)".
- **Regulated overlay**: HIPAA/SOX/PCI/SOC2/GDPR/FedRAMP tag in `TESTING.md` promotes `SHOULD` uncovered to P0 — see `rtm-personas-journeys.md` § "Regulated overlay".

## Resources

- `{baseDir}/references/taxonomy.md` — 7-layer canonical definitions
- `{baseDir}/references/layer-applicability.md` — classification → layer matrix
- `{baseDir}/references/testing-md-spec.md` — `tests/TESTING.md` schema
- `{baseDir}/references/rtm-personas-journeys.md` — RTM / personas / journeys spec
- `{baseDir}/references/discovery-preflight.md` — discovery and pre-flight checks
- `{baseDir}/references/github-audit.md` — repo-scoped audit engine
- `{baseDir}/references/test-quality-deep-audit.md` — bias, mutation, OWASP
- `{baseDir}/references/quality-gates-sweep.md` — tool catalog aligned to taxonomy
- `{baseDir}/references/philosophy.md` — Seven Walls derivations, escape-grammar state machine, Human/AI ownership rationale
- `{baseDir}/scripts/arch-check.sh` — architecture rule dispatcher
- `{baseDir}/scripts/bias-count.sh` — bias-pattern counter
- `{baseDir}/scripts/crap-score.py` — CRAP calculator
- `{baseDir}/scripts/gherkin-lint.sh` — advisory Gherkin quality check
- `{baseDir}/scripts/escape-scan.sh` — diff-based escape-attempt detector (reads floors from `tests/TESTING.md`)
- `{baseDir}/shared-refs/harness-hash.sh` — SHA-256 manifest verifier
- `{baseDir}/shared-refs/*.md` — per-concern deep references (frameworks, architecture, security, etc.) shared with `implement-tests`
