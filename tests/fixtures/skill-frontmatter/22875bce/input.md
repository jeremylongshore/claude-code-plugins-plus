---
name: implement-tests
description: "Filesystem-mutating test infrastructure installer. Accepts a structured\
  \ handoff payload from audit-tests OR direct invocation. Scaffolds frameworks, installs\
  \ tooling, wires CI, writes starter tests, initializes hash manifests across the\
  \ 7-layer testing taxonomy (git hooks \u2192 static \u2192 unit \u2192 integration\
  \ \u2192 system \u2192 E2E \u2192 acceptance). Stages all changes for engineer review\
  \ \u2014 never auto-commits. Use when implementing missing test layers, scaffolding\
  \ a new test suite, or installing specific testing tools. Trigger with \"implement\
  \ tests\", \"scaffold tests\", \"install testing system\", \"fill test gaps\", \"\
  set up CI\", \"install wall\", \"scaffold BDD\"."
version: 1.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
model: inherit
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(find:*), Bash(git:*), Bash(gh:*),
  Bash(ls:*), Bash(mkdir:*), Bash(chmod:*), Bash(sha256sum:*), Bash(curl:*), Bash(wget:*),
  Bash(pnpm:*), Bash(npm:*), Bash(npx:*), Bash(yarn:*), Bash(bun:*), Bash(pip:*),
  Bash(python:*), Bash(python3:*), Bash(pytest:*), Bash(go:*), Bash(cargo:*), Bash(bundle:*),
  Bash(mix:*), Bash(dotnet:*), Bash(make:*), Bash(bash:*), Task, AskUserQuestion,
  Skill
tags:
  - testing
  - implementation
  - scaffolding
  - installation
  - ci-wiring
compatibility: Designed for Claude Code
---

# implement-tests — Scaffold, Install, Wire (7-Layer)

**Invocation**: "implement tests" · "scaffold tests" · "install testing system" · "fill test gaps" · "set up CI" · "install wall N" · "scaffold BDD". Also fires automatically as the handoff target from `audit-tests` when P0/P1 gaps exist.

Run this skill to install the filesystem side of the 7-layer testing taxonomy. Parse the handoff payload (or the user's direct instruction), plan install order, install tooling, wire CI, write starter test artifacts, initialize the hash manifest. **Stage all changes for engineer review — never commit.**

## You are the engineer

Apply the same ownership model as `audit-tests`. The engineer owns the walls; this skill writes the glue. Keep every install reversible via `git restore`. Never modify policy sections of `tests/TESTING.md` or hash-pinned artifacts without engineer-initiated `audit-harness init`.

## Step 0.5 — Harness freshness check (automatic)

Run the same 24h-cached check from `audit-tests/SKILL.md` § "Step 0.5". If the target repo has an outdated harness, upgrade **before** running any install playbook — otherwise the L1/L3 configs you write will reference commands that may not exist in the old version. Node: `pnpm up @intentsolutions/audit-harness`. Vendored: re-run `install.sh` with the new `AUDIT_HARNESS_VERSION`.

## L0 — Install `@intentsolutions/audit-harness` into the target repo (mandatory)

**Before any other layer**, ensure the target repo has the enforcement harness installed. All L1/L3 hooks + CI reference in-repo commands, never `~/.claude/` paths.

### Node repos

```bash
pnpm add -D @intentsolutions/audit-harness
# or: npm install --save-dev @intentsolutions/audit-harness / yarn add --dev ...
```

Then invoke via `pnpm exec audit-harness <subcommand>`.

### Non-Node repos (Python, Go, Rust, Java, Ruby, C++, Elixir, .NET, shell, mixed)

```bash
curl -sSL https://raw.githubusercontent.com/jeremylongshore/audit-harness/main/install.sh | bash
# Pinned: AUDIT_HARNESS_VERSION=v0.1.0 curl -sSL .../install.sh | bash
```

This vendors `.audit-harness/` + creates `scripts/audit-harness` wrapper. Invoke via `scripts/audit-harness <subcommand>`.

### Verify install

```bash
pnpm exec audit-harness --version    # Node
scripts/audit-harness --version      # vendored
```

Record in `tests/TESTING.md#Installed gates` as `L0: @intentsolutions/audit-harness@X.Y.Z`.

## Invocation modes

### Mode A — Handoff from audit-tests (most common)

`audit-tests` calls this skill with a structured payload:

```json
{
  "classification": {"repo_type": "service", "languages": ["python", "typescript"]},
  "tests_md_path": "tests/TESTING.md",
  "p0_gaps": [
    {"layer": "L3", "gap": "no coverage gate configured"},
    {"layer": "L4-migration", "gap": "no migration tests"}
  ],
  "p1_gaps": [...],
  "rtm_gaps": [{"req_id": "REQ-002", "moscow": "MUST", "layers_missing": ["L3","L4"]}],
  "persona_gaps": [...],
  "journey_gaps": [...],
  "install_order": ["L1", "L2", "L3", "L4-migration", "L4-contract", "L6-smoke"],
  "user_confirm_required": false
}
```

The skill parses the payload via `scaffold-architect-agent`, then executes per layer.

### Mode B — Direct user invocation

When the user says "install husky + lint-staged" or "scaffold pytest + coverage + mutmut" or "set up the full testing system":

1. Detect the repo classification via `test-discovery-agent` (same as audit-tests Step 2).
2. Infer install scope from the user's words (specific tool named → just that; "full" → all applicable layers per `layer-applicability.md`).
3. Build a synthetic handoff payload and proceed as Mode A.

## Instructions

### Step 1 — Parse input

- If called via `Skill()` with a payload, read it directly.
- If called by the user, dispatch `test-discovery-agent` and `scaffold-architect-agent` to build the payload.
- Verify hash manifest: `bash {baseDir}/shared-refs/harness-hash.sh --verify`. If mismatch → halt with `HARNESS_TAMPERED`.

### Step 2 — Plan install order

Dispatch `scaffold-architect-agent` to:

- Resolve tool conflicts (e.g., Ruff vs Flake8 → prefer Ruff on new installs; if Flake8 already present, audit whether to migrate).
- Choose config file locations (prefer `pyproject.toml` for Python, `package.json` scripts for JS/TS, single-source configs).
- Linearize install order across layers (L1 depends on nothing, L2 depends on nothing, L3 depends on L1+L2 hooks, L4/L5/L6/L7 depend on L3).
- Output: ordered list of install actions `[(layer, tool, config, ci-step)]`.

### Step 3 — Install per layer

For each layer in order, load the playbook and dispatch `framework-installer-agent`:

| Layer                                 | Playbook                                                  |
| ------------------------------------- | --------------------------------------------------------- |
| L1 — Git hooks & CI enforcement       | `{baseDir}/references/install-playbook-L1-hooks.md`       |
| L2 — Static analysis & linting        | `{baseDir}/references/install-playbook-L2-static.md`      |
| L3 — Unit & function                  | `{baseDir}/references/install-playbook-L3-unit.md`        |
| L4 — Integration & regression         | `{baseDir}/references/install-playbook-L4-integration.md` |
| L5 — System quality                   | `{baseDir}/references/install-playbook-L5-system.md`      |
| L6 — E2E / BDD / Gherkin              | `{baseDir}/references/install-playbook-L6-e2e.md`         |
| L7 — Acceptance & business validation | `{baseDir}/references/install-playbook-L7-acceptance.md`  |

Each playbook is structured: detect language → install command per package manager → config snippet → CI wiring → starter artifact → validation command.

On install failure, `framework-installer-agent` reports the error; `scaffold-architect-agent` decides whether to:

- Retry with alternate install command (e.g., `pnpm` failed → try `npm`).
- Skip the tool and continue with an installation gap flagged in the final report.
- Halt (only for environment-wide issues like "no package manager available").

### Step 4 — Wire CI

Dispatch `ci-wiring-agent` to generate or update CI workflow files. Detects the CI platform:

| Signal                                          | Platform        | Output path                  |
| ----------------------------------------------- | --------------- | ---------------------------- |
| `.github/workflows/*.yml` exists or GitHub repo | GitHub Actions  | `.github/workflows/test.yml` |
| `.gitlab-ci.yml` exists                         | GitLab CI       | `.gitlab-ci.yml`             |
| `.circleci/config.yml` exists                   | CircleCI        | `.circleci/config.yml`       |
| `Jenkinsfile` exists                            | Jenkins         | `Jenkinsfile`                |
| `azure-pipelines.yml` exists                    | Azure Pipelines | `azure-pipelines.yml`        |

If no CI detected, default to GitHub Actions with a comment noting the assumption.

Each installed gate becomes a required check. Coverage / mutation / CRAP / architecture / escape-scan all run on PR.

### Step 5 — Scaffold starter artifacts

Dispatch `test-writer-agent`:

| Layer                                     | Starter artifact                                                                                                               |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| L3 (unit)                                 | 1–3 representative unit tests per public module, driven by existing function signatures                                        |
| L6 (BDD)                                  | One `.feature` file distilled from engineer-spoken intent (if captured) or scenario template derived from primary user journey |
| L7 (RTM scaffolding — first install only) | Skeleton `RTM.md`, `PERSONAS.md`, `JOURNEYS.md` via `rtm-scaffolder-agent`                                                     |

BDD starter feature: the **engineer owns scenarios** — the AI produces a template and prompts the engineer to refine. The template is hash-pinned immediately on `harness-hash.sh --init`.

### Step 6 — Write TESTING.md + initialize hash manifest

- If `tests/TESTING.md` doesn't exist: `rtm-scaffolder-agent` generates the full skeleton per `testing-md-spec.md`, with defaults in policy sections and a visible comment flagging them for engineer review.
- If `tests/TESTING.md` exists: update only the observational sections (`## Installed gates`, `## Frameworks`). Policy sections untouched.
- Initialize the hash manifest:

```bash
bash {baseDir}/shared-refs/harness-hash.sh --init
```

This pins the current state of `features/*.feature`, architecture-rule configs, and the policy sections of `TESTING.md` + `RTM.md`.

### Step 7 — Stage for engineer review (NEVER commit)

See `{baseDir}/references/auto-remediation.md` § 4 for the full stage-for-review protocol.

```
Review:   git status && git diff --staged
Commit:   git commit -m "..."   # engineer runs this
Discard:  git restore --staged .
```

### Step 8 — Report

Print the structured summary (layers installed, files staged, tests written, TESTING.md state). Hand control back to the user or caller.

## Specialist agents

| Agent                       | Responsibility                                                                                      |
| --------------------------- | --------------------------------------------------------------------------------------------------- |
| `scaffold-architect-agent`  | Plans install order; resolves tool conflicts; decides config locations                              |
| `framework-installer-agent` | Executes install commands for one layer; handles failure & retry                                    |
| `ci-wiring-agent`           | Generates / updates CI workflow YAML for detected platform                                          |
| `test-writer-agent`         | Writes starter tests (primarily L3 representative units + L6 `.feature` templates)                  |
| `rtm-scaffolder-agent`      | Generates initial `RTM.md` / `PERSONAS.md` / `JOURNEYS.md` + initial `TESTING.md` on fresh installs |

**Phase 2** (deferred): each agent upgrades to a full skill bundle with its own `SKILL.md` / `references/` / `scripts/` / `evals/`.

## What this skill refuses to do

- Commit (anywhere, ever — explicit v1.0.0 rule).
- Modify `features/*.feature` files (Wall 1, hash-pinned).
- Modify architecture rule configs (`.dependency-cruiser.js`, `.importlinter`, `deptrac.yaml`, ArchUnit rules).
- Modify policy sections of `TESTING.md` or `RTM.md`.
- Lower coverage / mutation / CRAP thresholds.
- Install a layer that `TESTING.md` explicitly waives.
- Push to remote.
- Touch files outside the repo root.

Anything in this list triggers a refusal + escape-scan report.

## Output

### Successful install

```
═══════════════════════════════════════════════════════
  IMPLEMENT-TESTS v1.0.0 — STAGED FOR REVIEW
═══════════════════════════════════════════════════════
Repo:         my-service (service / python + typescript)
Install set:  L1, L2, L3, L4-integration, L6-smoke

Layer        Tool(s)                      Status
L1           husky@9 + lint-staged        installed
L2           ruff + mypy + gitleaks       installed
L3           pytest + coverage + mutmut   installed
L4-integ     testcontainers               installed (postgres fixture)
L6-smoke     playwright                   installed

Files staged: 18
Tests written: 12 starter + 3 .feature templates (engineer to refine)
TESTING.md:   written (policy defaults flagged for review)
CI:           .github/workflows/test.yml generated (8 required checks)
Hash manifest: initialized (pinned: features/, .dependency-cruiser.js, TESTING.md#policy)

Review:  git status && git diff --staged
Commit:  your call
═══════════════════════════════════════════════════════
```

### Partial install (one tool failed)

```
IMPLEMENT-TESTS — PARTIAL
L3 → pytest + coverage installed; mutmut failed (network timeout)
Recommend:  retry mutmut install manually or run:
            Skill(implement-tests, args={"install_order":["L3-mutation"]})
```

## Examples

**Example 1 — Greenfield Python library (handoff from audit-tests).**
Invoked by `audit-tests` with `install_order: [L1, L2, L3]`. Executes pre-commit + husky setup, installs ruff + mypy + gitleaks + radon, pytest + coverage + mutmut + hypothesis + import-linter. Writes `pyproject.toml` sections, `.pre-commit-config.yaml`, `.importlinter`, and `.github/workflows/test.yml` with 6 required-check jobs. Scaffolds `tests/TESTING.md` + `RTM.md` + `PERSONAS.md` skeletons. Writes 9 starter unit tests. Stages 18 files. Prints the stage-for-review summary. No git commit executed.

**Example 2 — Single-tool direct invocation.**
User says `install husky + lint-staged + commitlint`. `scaffold-architect-agent` infers scope as L1 only. `framework-installer-agent` runs `pnpm add -D husky lint-staged @commitlint/cli @commitlint/config-conventional`. Writes `.husky/pre-commit`, `.husky/commit-msg`, `commitlint.config.js`. Adds `prepare` script to `package.json`. No other layer touched. 4 files staged for review.

**Example 3 — Partial install due to network failure.**
Invoked with `install_order: [L3]`. `pytest` + `coverage.py` install succeeds. `mutmut` install times out; `framework-installer-agent` retries once, fails again. Report: `L3 partial — mutmut install pending (ECONNRESET after retry)`. CI yaml adds the `mutation` job with a comment `# TODO: re-run install before merge`. Report includes engineer next-step: "Retry mutmut install manually once network is stable."

**Example 4 — User requests policy change (refused).**
User says `implement tests: lower coverage.line to 60`. Skill refuses, prints: "Policy sections of `tests/TESTING.md` are engineer-owned. Edit manually, then run `bash ~/.claude/skills/audit-tests/shared-refs/harness-hash.sh --init` to re-pin." No filesystem changes made.

**Example 5 — Monorepo with one shared root ESLint config.**
`audit-tests` handoff payload contains per-package `install_order`. `scaffold-architect-agent` detects shared `.eslintrc.js` at root — installs ESLint once at root, symlinks / references from each package config. Each package's `jest.config.ts` installed independently. One root `.github/workflows/test.yml` with matrix strategy over packages.

## Troubleshooting

| Symptom                                                 | Diagnosis                                                         | Fix                                                                                                                                    |
| ------------------------------------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `framework-installer-agent` reports `ECONNRESET`        | Network timeout during package install.                           | Retry once triggered automatically; if second fails, install manually or re-run skill with `--offline` if packages are cached locally. |
| Hash mismatch after implement-tests run                 | Engineer edited policy during install; hash now out of sync.      | Engineer runs `harness-hash.sh --init` after reviewing the staged diff.                                                                |
| CI yaml didn't include a new job                        | `ci-wiring-agent` didn't know about the new gate.                 | Re-run the skill with an explicit `install_order: [gate-name]`; or edit the CI yaml by hand.                                           |
| `.husky/pre-commit` not executing                       | Husky not initialized properly — `pnpm prepare` didn't run.       | Run `pnpm prepare` manually, or ensure `"prepare": "husky"` is in `package.json#scripts`.                                              |
| Starter tests fail on first run                         | Test-writer generated templates that require real source imports. | Starter tests are labelled `@starter` — adjust imports to match actual module paths; the tests are intentionally minimal.              |
| `rtm-scaffolder-agent` declined to overwrite `RTM.md`   | Engineer-content detected in existing file.                       | Correct behavior. To regenerate, delete `RTM.md` first, then re-run with `scaffold RTM`.                                               |
| Audit-tests did not trigger this skill on a feat branch | Audit-tests found no P0/P1 gaps.                                  | Run `implement-tests` directly with an explicit layer request.                                                                         |

## Edge cases

- **Network unreachable during install**: fall back to "config-only" mode — write configs, skip package installs, flag each as "install pending" in the report. Engineer completes installation offline.
- **Tool conflict**: if existing repo already uses Flake8, do not auto-migrate to Ruff. Report the gap and let engineer choose.
- **Monorepo with shared root config**: install at root; symlink into package dirs only if necessary.
- **Engineer-waived layer appears in handoff payload**: silently skip with "honored `TESTING.md#Waived layers`" note in report.

## Resources

- `{baseDir}/references/auto-remediation.md` — gap-to-test pipeline, verification loop, stage-for-review protocol (no auto-commit in v1.0.0)
- `{baseDir}/references/scaffold-productivity.md` — productivity audit and scaffold when no tests exist
- `{baseDir}/references/rtm-templates.md` — template library for `RTM.md` / `PERSONAS.md` / `JOURNEYS.md`
- `{baseDir}/references/install-playbook-L1-hooks.md` — git hooks & CI enforcement playbook
- `{baseDir}/references/install-playbook-L2-static.md` — static analysis & linting playbook
- `{baseDir}/references/install-playbook-L3-unit.md` — unit / coverage / mutation / CRAP / architecture playbook
- `{baseDir}/references/install-playbook-L4-integration.md` — integration / contract / migration / IaC playbook
- `{baseDir}/references/install-playbook-L5-system.md` — perf / security / a11y / chaos playbook
- `{baseDir}/references/install-playbook-L6-e2e.md` — E2E / BDD / visual playbook
- `{baseDir}/references/install-playbook-L7-acceptance.md` — UAT + automated acceptance + RTM scaffolding playbook
- `{baseDir}/shared-refs/` — full set of per-concern deep references shared with `audit-tests`
- `{baseDir}/shared-refs/harness-hash.sh` — SHA-256 manifest init + verify
