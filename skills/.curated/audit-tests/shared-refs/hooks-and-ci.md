# Pre-Commit Hooks and CI/CD Enforcement

## Contents

[Purpose](#purpose) · [Pre-Commit Hook Frameworks](#pre-commit-hook-frameworks) · [Commit Conventions](#commit-conventions) · [CI/CD Platform Audits](#cicd-platform-audits) · [Required CI Gates](#required-ci-gates) · [Monorepo CI Patterns](#monorepo-ci-patterns) · [Supply-Chain & Provenance](#supply-chain--provenance) · [Enforcement Checklist](#enforcement-checklist) · [Sources](#sources)

## Purpose

A passing test suite means nothing if it doesn't run before merge.
Pre-commit hooks enforce local discipline; CI enforces it at the PR
boundary. This reference catalogs every hook framework + every CI platform
the sweep expects to see, and what gates must be present for a repo to
pass audit.

## Pre-Commit Hook Frameworks

### 1. Husky (JavaScript / Node.js)

Canonical in the Node ecosystem. Requires git + npm.

```bash
pnpm add -D husky lint-staged
pnpm exec husky init

# .husky/pre-commit
echo 'pnpm lint-staged' > .husky/pre-commit
chmod +x .husky/pre-commit
```

`.lintstagedrc.json`:

```json
{
  "*.{ts,tsx,js,jsx}": ["eslint --fix", "prettier --write"],
  "*.{json,md,yml,yaml}": ["prettier --write"],
  "*.sh": ["shellcheck", "shfmt -w"]
}
```

### 2. lefthook (Cross-language, Go binary)

Faster than Husky, language-agnostic. Works well for polyglot repos.

```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    lint-js:
      glob: "*.{ts,js,tsx,jsx}"
      run: npx eslint --fix {staged_files}
      stage_fixed: true
    lint-py:
      glob: "*.py"
      run: ruff check --fix {staged_files} && ruff format {staged_files}
      stage_fixed: true
    gitleaks:
      run: gitleaks protect --staged --verbose
```

Install: `brew install lefthook` or `go install`; then `lefthook install`.

### 3. pre-commit (Python framework, language-agnostic)

The gold standard for Python and heterogeneous repos. Maintained by
Yelp, used by most major OSS projects.

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.9
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
```

Install: `pipx install pre-commit && pre-commit install`.

Auto-update: `pre-commit autoupdate` (pin SHAs for deterministic builds).

### 4. simple-git-hooks (minimal JS)

Lightweight Husky alternative. One `package.json` field:

```json
"simple-git-hooks": {
  "pre-commit": "pnpm lint-staged",
  "commit-msg": "npx commitlint --edit $1"
}
```

### 5. Native git hooks

Last resort. Place shell scripts in `.git/hooks/` or `core.hooksPath`. No
distribution mechanism — every clone must re-install.

### 6. Captain Hook (PHP)

PHP-ecosystem hook runner; reads `captainhook.json`.

### 7. overcommit (Ruby)

Ruby-ecosystem hook runner; reads `.overcommit.yml`.

### Decision matrix

| Repo type | Recommended |
|---|---|
| Pure JS/TS Node | **Husky + lint-staged** (ecosystem fit) |
| Pure Python | **pre-commit framework** (ecosystem fit) |
| Polyglot | **lefthook** (parallel, fast, language-agnostic) or **pre-commit framework** |
| Ruby/Rails | **overcommit** (ecosystem fit) |
| PHP | **Captain Hook** |
| Everything else | **lefthook** or **pre-commit framework** |

## Commit Conventions

### Conventional Commits

The dominant spec: `<type>[scope]: <description>` (e.g., `feat(auth): add OIDC`).

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`,
`ci`, `chore`, `revert`.

### Enforcement tools

| Tool | Mechanism |
|---|---|
| **commitlint** (JS) | `.husky/commit-msg` runs `npx commitlint --edit $1` |
| **commitizen** (JS/Py) | Interactive commit via `cz` command |
| **gitlint** (Python) | Shell wrapper; config in `.gitlint` |
| **go-commitlint** (Go) | native Go binary |

commitlint install:

```bash
pnpm add -D @commitlint/cli @commitlint/config-conventional
echo "export default { extends: ['@commitlint/config-conventional'] };" > commitlint.config.js
echo 'npx commitlint --edit $1' > .husky/commit-msg
```

### Release automation

- **semantic-release** — auto-version + changelog + npm publish on main push
- **release-please** (Google) — similar, via PR
- **changesets** — designed for monorepos with independent packages
- **commitizen** (Py) — `cz bump` pattern

Mega-skill expectation: a release-grade repo has `feat:`/`fix:`/`BREAKING CHANGE:`
commits driving automatic version bumps.

## CI/CD Platform Audits

### GitHub Actions

Signal: `.github/workflows/*.yml`

Audit checks:

1. **Does a CI workflow exist?** (at least one `.yml` under workflows)
2. **Does it run on PR + push to main?** (`on: [pull_request, push]`)
3. **Does it install deps before running tests?**
4. **Does each required gate run?** (lint, format-check, type, test, security, coverage)
5. **Does `continue-on-error: true` appear?** (red flag — means gate can fail silently)
6. **Are secrets read via `${{ secrets.* }}`?** (no inline)
7. **Is there a matrix for multi-OS / multi-version?** (nice-to-have, P2)
8. **Are caches configured?** (`actions/cache`, `setup-node` cache, `setup-python` cache)
9. **Is there a release workflow?** (tag-triggered)
10. **Is Dependabot / Renovate enabled?** (`.github/dependabot.yml` or `renovate.json`)

Minimum viable `.github/workflows/ci.yml`:

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm format:check
      - run: pnpm typecheck
      - run: pnpm test -- --coverage
      - uses: codecov/codecov-action@v4
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: gitleaks/gitleaks-action@v2
      - uses: aquasecurity/trivy-action@master
        with: { scan-type: fs, severity: CRITICAL,HIGH, exit-code: 1 }
```

### GitLab CI

Signal: `.gitlab-ci.yml`

Stages typically: `build → test → security → deploy`. Check `rules:` for
MR-only vs push. Check `allow_failure: true` (same anti-pattern as
`continue-on-error`).

### CircleCI

Signal: `.circleci/config.yml`

Uses orbs (reusable workflow packages). Audit for the CI-language orb
(e.g., `circleci/node@5.1`, `circleci/python@2.1`) — if missing, the
repo is rolling its own install from scratch.

### Jenkins

Signal: `Jenkinsfile`

Scripted vs declarative pipelines. Check `agent { docker { ... } }` for
reproducibility. Check for `sh '... || true'` (ignored failures).

### Azure Pipelines

Signal: `azure-pipelines.yml` or `.azure/pipelines/*.yml`.

### Travis CI

Signal: `.travis.yml`. Effectively legacy — public repos migrated to GHA
in 2020-2021. Presence may indicate the CI config is stale.

### Buildkite

Signal: `.buildkite/pipeline.yml`.

### Drone CI

Signal: `.drone.yml` / `.drone.yaml`.

### Tekton (Kubernetes-native)

Signal: `PipelineRun` / `Task` CRDs in `tekton/` or similar.

### Argo Workflows

Signal: `workflow.yaml` with `apiVersion: argoproj.io/v1alpha1`.

## Required CI Gates

The sweep expects these gates to be wired into CI, each failing the build
on non-zero exit. P0 = must have for any release-grade repo.

| Gate | Priority | Signal |
|---|---|---|
| Lint | **P0** | `ruff`, `eslint`, `golangci-lint`, etc. step |
| Format check (non-fixing) | **P0** | `prettier --check`, `ruff format --check`, `gofmt -l`, `cargo fmt --check` |
| Type check | **P0** (if typed language) | `tsc --noEmit`, `mypy`, `cargo check`, `go vet` |
| Unit tests | **P0** | test runner step with non-zero exit |
| Integration tests | **P0** (if repo has integration) | separate job or stage |
| E2E tests | **P1** (if repo has UI) | Playwright / Cypress step |
| Coverage gate | **P0** | `--cov-fail-under`, `coverageThreshold`, JaCoCo `minimum`, `cargo-tarpaulin --fail-under` |
| Mutation | **P1** | Stryker / mutmut / PITest step (may be scheduled, not per-PR) |
| Security SAST | **P0** | Semgrep / CodeQL / Bandit / gosec / Brakeman |
| Secrets scan | **P0** | gitleaks / trufflehog |
| Dep vuln scan | **P0** | `npm audit`, `pip-audit`, `cargo audit`, `govulncheck`, Snyk, Trivy |
| Container scan | **P0** (if Docker) | Trivy / Grype / Docker Scout |
| IaC scan | **P0** (if Terraform/K8s) | Checkov / tfsec / kube-score |
| Accessibility | **P1** (if UI) | axe-core / Lighthouse |
| License check | **P2** | FOSSA / licensed / license-finder |
| SBOM | **P1** | CycloneDX / Syft |

## Monorepo CI Patterns

### Nx

Signal: `nx.json`, `project.json` in each workspace.

Affected-only runs: `nx affected:test`, `nx affected:lint`. Audit for
`.nxignore` and remote cache config.

### Turborepo

Signal: `turbo.json`, `pnpm-workspace.yaml`.

Filter by changes: `turbo run test --filter=[origin/main]`.

### Bazel

Signal: `WORKSPACE`, `BUILD.bazel`, `MODULE.bazel`.

Audit for remote cache (`--remote_cache=...`) and query-based PR filtering
(`bazel query 'rdeps(//..., <changed>)'`).

### Rush / Lerna (legacy)

Signal: `rush.json` (Rush), `lerna.json` (Lerna).

## Supply-Chain & Provenance

Increasingly expected in CI:

- **SBOM** — Syft (`syft .`), CycloneDX (`cyclonedx-gomod`, `cyclonedx-npm`, `cyclonedx-python`), SPDX
- **SLSA provenance** — in-toto attestations, `slsa-framework/slsa-github-generator`
- **Signed containers** — Cosign + Sigstore (keyless signing via OIDC)
- **Artifact signing** — GPG, Minisign, Cosign
- **Reproducible builds** — deterministic artifacts; `diffoscope` to verify

GitHub Actions example (Cosign keyless):

```yaml
- uses: sigstore/cosign-installer@v3
- run: cosign sign --yes ${{ env.IMAGE }}
  env:
    COSIGN_EXPERIMENTAL: 1
```

## Enforcement Checklist

For every repo audited, verify:

- [ ] At least one pre-commit framework is installed
- [ ] Pre-commit config exists and runs at least lint + format + secrets scan
- [ ] Pre-commit is distributed (in repo, not `.git/hooks/` only)
- [ ] Commit-msg convention is enforced (commitlint, gitlint)
- [ ] CI workflow file exists on the canonical platform (`.github/workflows/*.yml` etc.)
- [ ] CI runs on both PR and push to main
- [ ] All P0 gates from the table above run with failing exit codes
- [ ] No gate uses `continue-on-error: true` / `allow_failure: true`
- [ ] Dependabot / Renovate config present
- [ ] Secrets accessed only via platform secrets system
- [ ] Caches configured (setup-* actions, custom `actions/cache`)
- [ ] Release workflow exists (tag or main-push triggered)
- [ ] SBOM + artifact signing (for release-grade repos)
- [ ] Branch protection enforces CI pass before merge (check via `gh api`)

Missing P0 items are reported and offered for installation.

## Sources

- Conventional Commits spec — conventionalcommits.org
- SLSA levels — slsa.dev
- Sigstore — sigstore.dev
- OpenSSF Scorecard — github.com/ossf/scorecard (automated CI-gate audit)
- CNCF Cloud-Native CI/CD Guide
- Google SRE Workbook, ch. 15 "Managing Load" — pipeline reliability patterns.
