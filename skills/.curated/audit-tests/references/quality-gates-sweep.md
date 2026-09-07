# Quality Gate Sweep — Per-Category Tool Catalog (Aligned to 7-Layer Taxonomy)

> **v7 alignment (2026-04):** This file is a tool-and-command catalog; the **authoritative structure** for `audit-tests` is now `taxonomy.md` (7-layer pyramid). The 10 categories below map directly onto the 7 layers as shown in the mapping table. Use `taxonomy.md` for classification + gap-mapping; use this file for "what tool do I reach for in language X, category Y?"
>
> **Mapping:**
>
> | Sweep category | Taxonomy layer |
> |---|---|
> | 1. Unit tests | L3 |
> | 2. Integration & infra | L4 (integration + migration + IaC) |
> | 3. E2E / UI | L6 |
> | 4. API / contract | L4-contract |
> | 5. Perf / load / chaos | L5-perf + L5-chaos |
> | 6. Mutation + PBT + fuzz | L3 (mutation, PBT) + L3-fuzz |
> | 7. Static analysis | L2 |
> | 8. Pre-commit + CI depth | L1 |
> | 9. Security | L2-secrets/deps + L5-sec |
> | 10. Accessibility + visual | L5-a11y + L6-visual |

## Contents

[Philosophy](#philosophy) · [The Ten Categories](#the-ten-categories) · [Per-Language Shopping Lists](#per-language-shopping-lists) · [Sweep Protocol](#sweep-protocol) · [Detection Heuristics](#detection-heuristics) · [Install Matrix](#install-matrix) · [Cross-References](#cross-references) · [Sources](#sources)

## Philosophy

> **Every test layer that could exist in a repo must be audited.** Present,
> absent, configured, unused, stale, bypassed — the sweep catalogs all of
> it. The 7-layer taxonomy (see `taxonomy.md`) is the authoritative pyramid;
> the walls (acceptance / unit / coverage / mutation / CRAP / architecture)
> are invariants that live *inside* layers L3 and L6–L7. A repo can pass
> every wall and still be missing prettier, husky, gitleaks, or a coverage
> gate in CI. This sweep finds those gaps.

The walls answer *"can this codebase's tests be trusted?"*. The Quality
Gate Sweep answers *"is every quality layer that should exist actually
present, running, and enforced?"*.

## The Ten Categories

| # | Category | Reference | Example Tools |
|---|---|---|---|
| 1 | **Unit tests** | `frameworks.md` | pytest, vitest, jest, go test, cargo test, JUnit, RSpec, PHPUnit, ExUnit, xUnit |
| 2 | **Integration & infra tests** | `integration-and-infra.md` | testcontainers, pytest-docker, wiremock, terratest, InSpec, kube-bench |
| 3 | **E2E / UI tests** | `e2e-testing.md` | Playwright, Cypress, WebdriverIO, Selenium, Puppeteer |
| 4 | **API / contract tests** | `specialized-testing.md` § API | Dredd, Pact, Postman/Newman, Supertest, REST-Assured, Schemathesis |
| 5 | **Performance / load / chaos** | `specialized-testing.md` § Perf + `property-and-fuzz.md` § Chaos | k6, Artillery, Locust, JMeter, Gatling, Chaos Mesh, Litmus, Pumba |
| 6 | **Mutation + property-based + fuzz** | `test-quality-deep-audit.md` + `property-and-fuzz.md` | Stryker, mutmut, PITest, cargo-mutants, Hypothesis, fast-check, proptest, AFL, libFuzzer |
| 7 | **Static analysis (lint / format / types)** | `linters-formatters-types.md` | ESLint, Prettier, Ruff, Black, Clippy, gofmt, RuboCop, Checkstyle, tsc, mypy, pyright, ShellCheck, hadolint |
| 8 | **Pre-commit hooks + CI/CD enforcement** | `hooks-and-ci.md` | Husky, lefthook, pre-commit (py), commitlint, GitHub Actions, GitLab CI, CircleCI, Jenkins |
| 9 | **Security (SAST / DAST / secrets / deps / container / IaC)** | `security-testing.md` | Semgrep, CodeQL, ZAP, gitleaks, Trivy, Snyk, Checkov, tfsec |
| 10 | **Accessibility + visual regression** | `specialized-testing.md` § A11y + § Visual | axe-core, pa11y, Lighthouse, Percy, Chromatic, BackstopJS, Applitools |

**Wall 1** (Gherkin acceptance — `acceptance-tests-gherkin.md`), **Walls
3/4** (coverage + mutation — `test-quality-deep-audit.md`), **Walls 5/6**
(CRAP — `crap-and-complexity.md`), and **Wall 7** (architecture —
`architecture-constraints.md`) remain the structural doctrine. This sweep
*supplements* them with comprehensive coverage scanning.

## Per-Language Shopping Lists

The complete set of gates a repo *should* have, by primary language. The
sweep reports gaps against this list.

### JavaScript / TypeScript (Node.js / Deno / Bun)

| Category | Expected tool(s) |
|---|---|
| Unit | Vitest / Jest / Mocha / node:test |
| E2E | Playwright / Cypress / WebdriverIO |
| API | Supertest / Pact |
| Perf | k6 / Artillery |
| Mutation | Stryker |
| Property | fast-check |
| Fuzz | Jazzer.js |
| Snapshot / visual | jest snapshot / Playwright visual / Percy / Chromatic |
| Linter | ESLint (or Biome or oxlint) |
| Formatter | Prettier (or Biome) |
| Type checker | tsc (`--noEmit`) |
| Pre-commit | Husky + lint-staged (or lefthook / simple-git-hooks) |
| Commit convention | commitlint + Conventional Commits |
| Secrets scan | gitleaks |
| Dep audit | `npm audit` / `pnpm audit` / Snyk / OSV-scanner |
| Container | Trivy / Grype (if Docker) |
| IaC | Checkov / tfsec (if Terraform) |
| CI workflow | `.github/workflows/` must run: lint + format + type + unit + integration + e2e + security + coverage gate |

### Python

| Category | Expected tool(s) |
|---|---|
| Unit | pytest (+ pytest-cov, pytest-xdist, pytest-mock) |
| Integration | pytest + testcontainers-python / pytest-docker |
| E2E | Playwright-Python |
| API | requests/httpx + Schemathesis / Pact-Python |
| Perf | Locust |
| Mutation | mutmut (or cosmic-ray) |
| Property | Hypothesis |
| Fuzz | Atheris |
| Linter | **Ruff** (preferred) or Flake8 + Pylint |
| Formatter | **Ruff format** (or Black) + isort |
| Type checker | mypy (or pyright) |
| Pre-commit | `pre-commit` framework (pre-commit.com) |
| Secrets | gitleaks / detect-secrets |
| Dep audit | `pip-audit` / Safety / Snyk |
| Security SAST | Bandit |
| CI | GH Actions / GitLab CI with: ruff + mypy + pytest + coverage + bandit + pip-audit |

### Rust

| Category | Expected tool(s) |
|---|---|
| Unit | `cargo test` + proptest for property |
| Integration | `tests/` directory |
| Mutation | cargo-mutants |
| Fuzz | cargo-fuzz / afl.rs |
| Linter | Clippy (`cargo clippy -- -D warnings`) |
| Formatter | rustfmt |
| Type | rustc (built-in) |
| Dep audit | `cargo audit` + `cargo deny` |
| Pre-commit | lefthook or native hooks |
| CI | `cargo check && cargo clippy && cargo fmt --check && cargo test && cargo audit` |

### Go

| Category | Expected tool(s) |
|---|---|
| Unit | `go test ./...` + testify |
| Integration | testcontainers-go |
| E2E BDD | godog |
| Mutation | go-mutesting |
| Property | testing/quick + gopter |
| Fuzz | `go test -fuzz` (native, Go 1.18+) |
| Linter | golangci-lint (umbrella: staticcheck, errcheck, ineffassign, revive) |
| Formatter | gofmt + goimports (or gofumpt) |
| Type | compiler |
| Dep audit | govulncheck + nancy |
| Pre-commit | lefthook |
| CI | gofmt check + go vet + golangci-lint + go test + govulncheck + coverage |

### Ruby

| Category | Expected tool(s) |
|---|---|
| Unit | RSpec / Minitest |
| Integration | rails-controller-testing + capybara |
| E2E | Capybara + Selenium/Cuprite |
| Mutation | Mutant |
| Property | rantly |
| Linter | RuboCop (or Standard) |
| Formatter | RuboCop / rufo |
| Static analysis | Reek / Brakeman (security) |
| Type | Sorbet / RBS |
| Pre-commit | Lefthook / overcommit |
| Dep audit | bundle-audit |
| CI | RuboCop + Brakeman + RSpec + bundle-audit + SimpleCov |

### Java / Kotlin

| Category | Expected tool(s) |
|---|---|
| Unit | JUnit 5 / Spock (Groovy) / Kotest (Kotlin) |
| Integration | Testcontainers-Java |
| E2E BDD | Cucumber-JVM |
| Mutation | PITest |
| Property | jqwik |
| Linter | Checkstyle + PMD + SpotBugs + ErrorProne |
| Formatter | google-java-format or Spotless |
| Type | compiler |
| Dep audit | OWASP Dependency-Check / Snyk |
| Arch | ArchUnit |
| Build | Gradle / Maven with JaCoCo coverage gate |
| CI | Gradle pipeline: compile + checkstyle + spotbugs + test + pitest + jacoco + dependencyCheck |

### PHP

| Category | Expected tool(s) |
|---|---|
| Unit | PHPUnit / Pest |
| E2E | Codeception + Selenium |
| Mutation | Infection |
| Linter | PHPStan (level 8+) or Psalm |
| Formatter | php-cs-fixer / PHP_CodeSniffer |
| Pre-commit | Captain Hook / pre-commit |
| Dep audit | Roave Security Advisories |
| CI | phpstan + php-cs-fixer --dry-run + phpunit + infection |

### Elixir

| Category | Expected tool(s) |
|---|---|
| Unit | ExUnit |
| Property | StreamData |
| Linter | Credo |
| Formatter | `mix format` |
| Type | Dialyzer (via dialyxir) |
| Security SAST | Sobelow (Phoenix) |
| Dep audit | `mix hex.audit` / mix_audit |
| CI | format --check + credo + dialyzer + test + sobelow |

### .NET (C# / F# / VB)

| Category | Expected tool(s) |
|---|---|
| Unit | xUnit / NUnit / MSTest |
| Property | FsCheck |
| E2E BDD | Reqnroll (SpecFlow successor) |
| Mutation | Stryker.NET |
| Linter | Roslyn analyzers + StyleCop |
| Formatter | `dotnet format` |
| Dep audit | `dotnet list package --vulnerable` + Snyk |
| CI | dotnet format + build + test + stryker + dependabot |

### C / C++

| Category | Expected tool(s) |
|---|---|
| Unit | GoogleTest / Catch2 / doctest |
| Fuzz | libFuzzer / AFL++ / OSS-Fuzz |
| Linter | clang-tidy + cppcheck |
| Formatter | clang-format |
| Static analysis | scan-build / CodeChecker / SonarQube |
| Sanitizers | ASan + UBSan + TSan + MSan |
| CI | clang-format --dry-run + clang-tidy + build with sanitizers + GoogleTest + coverage (lcov) |

### Shell / Bash

| Category | Expected tool(s) |
|---|---|
| Test | Bats-core / shunit2 |
| Linter | **ShellCheck** |
| Formatter | shfmt |
| CI | shellcheck **/*.sh + shfmt -d + bats test/ |

### Infrastructure-as-Code

| IaC Type | Expected gates |
|---|---|
| Terraform | `terraform fmt -check` + `terraform validate` + tflint + tfsec + Checkov + Terratest |
| Kubernetes | kubeconform + kube-score + polaris + kube-bench (CIS) + Datree |
| Helm | `helm lint` + kubeval on rendered output + Checkov |
| Ansible | ansible-lint + molecule (test framework) |
| Docker | hadolint + Trivy (image) + docker-scout |
| CloudFormation | cfn-lint + cfn-nag |

## Sweep Protocol

The Quality Gate Sweep runs after framework execution and before GitHub
Audit. Step 5.5 in the SKILL.md pipeline.

### 5.5.1 — Discover primary languages

Use `discovery-preflight.md` output. For each detected language, look up
the shopping list above.

### 5.5.2 — Walk every category

For each of the 10 categories, check:

1. **Presence** — is a tool installed? (package manifest, `which`, config file)
2. **Configuration** — is it configured? (config file, not just installed)
3. **Wiring** — is it called from CI? (grep CI workflows)
4. **Enforcement** — does failure fail the build? (exit code check, continue-on-error flags)
5. **Staleness** — when was the config last touched? (git log -1 on config)

### 5.5.3 — Report format

Produce `QUALITY_GATES.md` at repo root alongside `TEST_AUDIT.md`:

```markdown
# Quality Gates Audit

**Primary language:** [detected]
**Sweep date:** [ISO-8601]

## Category coverage (P0 = blocking, P1 = should have, P2 = nice to have)

| Category | Tool found | Configured | Wired to CI | Enforced | Gap? |
|---|---|---|---|---|---|
| Unit tests | pytest | ✅ pyproject.toml | ✅ .github/workflows/ci.yml | ✅ exit 1 on fail | — |
| Linter | — | — | — | — | P0: install Ruff |
| Formatter | Black | ✅ | ⚠️ not in CI | — | P1: add to CI |
| Type checker | — | — | — | — | P0: install mypy |
| Pre-commit | — | — | — | — | P1: install pre-commit framework |
| Secrets scan | — | — | — | — | P0: install gitleaks |
| Dep audit | — | — | — | — | P0: add pip-audit |
| ... |
```

### 5.5.4 — Remediation plan

For each P0 gap, emit:

- Install command (verbatim shell)
- Minimal config (file + content)
- CI wiring (YAML snippet)
- Validation command

IMPLEMENT mode: scaffold the config files + CI steps for engineer review.
AUDIT mode: report only.

## Detection Heuristics

Gate presence is inferred from these signals (rough priority order):

### JavaScript / TypeScript

- **ESLint**: `.eslintrc*`, `eslint.config.js`, `"eslint"` in `package.json` devDeps
- **Prettier**: `.prettierrc*`, `.prettier.config.js`, `"prettier"` in deps
- **Biome**: `biome.json`
- **Husky**: `.husky/` dir, `"husky"` in devDeps
- **lint-staged**: `.lintstagedrc*` or `lint-staged` key in package.json
- **commitlint**: `commitlint.config.js` or `.commitlintrc*`

### Python

- **Ruff**: `ruff.toml`, `pyproject.toml` `[tool.ruff]`
- **Black**: `pyproject.toml` `[tool.black]`
- **mypy**: `mypy.ini`, `pyproject.toml` `[tool.mypy]`
- **pre-commit**: `.pre-commit-config.yaml`
- **pytest**: `pyproject.toml` `[tool.pytest]`, `pytest.ini`, `setup.cfg [tool:pytest]`
- **Bandit**: `.bandit` or `pyproject.toml` `[tool.bandit]`

### Rust

- **Clippy**: `.cargo/config.toml` or `clippy.toml`; on by default via rustup
- **rustfmt**: `rustfmt.toml` or `.rustfmt.toml`
- **cargo audit**: `deny.toml` (for cargo-deny)

### Go

- **golangci-lint**: `.golangci.yml` / `.golangci.toml`
- **goreleaser**: `.goreleaser.yml`

### Everywhere

- **gitleaks**: `.gitleaks.toml`, `.github/workflows/*gitleaks*`
- **Trivy**: `.trivyignore`, workflow file reference
- **Checkov**: `.checkov.yml`
- **Semgrep**: `.semgrep.yml`
- **pre-commit.com**: `.pre-commit-config.yaml`
- **CodeQL**: `.github/workflows/codeql-analysis.yml`

## Install Matrix

One-liners to install missing gates, per ecosystem.

### Node / TypeScript

```bash
# Full install of a quality-gated Node project
pnpm add -D \
  eslint @eslint/js typescript-eslint \
  prettier \
  typescript \
  vitest @vitest/coverage-v8 \
  husky lint-staged \
  @commitlint/cli @commitlint/config-conventional

# Initialize
pnpm exec husky init
echo 'pnpm lint-staged' > .husky/pre-commit
echo '{ "*.{js,ts,tsx}": ["eslint --fix", "prettier --write"] }' > .lintstagedrc
```

### Python

```bash
# Using uv (modern) or pip
uv add --dev ruff mypy pytest pytest-cov hypothesis bandit pip-audit pre-commit

# Initialize pre-commit
pre-commit sample-config > .pre-commit-config.yaml
pre-commit install
```

### Rust

```bash
# rustup ships clippy + rustfmt; add cargo-mutants + cargo-audit
cargo install cargo-mutants cargo-audit cargo-deny cargo-fuzz
```

### Go

```bash
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
go install golang.org/x/vuln/cmd/govulncheck@latest
# Native fuzz: `go test -fuzz=.` — Go 1.18+
```

### Cross-language

```bash
# gitleaks (secrets)
brew install gitleaks              # mac
docker run zricethezav/gitleaks:latest

# trivy (deps + containers + IaC)
brew install trivy

# pre-commit (language-agnostic hook runner)
pipx install pre-commit

# semgrep (SAST)
brew install semgrep
```

## Cross-References

- `linters-formatters-types.md` — full per-language detail for category 7
- `hooks-and-ci.md` — full detail for category 8
- `security-testing.md` — full detail for category 9
- `integration-and-infra.md` — full detail for category 2
- `property-and-fuzz.md` — property-based + fuzz + chaos (categories 5, 6)
- `frameworks.md` — unit test commands per language (category 1)
- `e2e-testing.md` — E2E runners (category 3)
- `specialized-testing.md` — contract / perf / a11y / visual / mutation (categories 4, 5, 6, 10)
- `github-audit.md` — wider repo-level audit (this file focuses on gates specifically)

## Sources

- OWASP SAMM — Software Assurance Maturity Model, v2.
- CIS Benchmarks — Center for Internet Security baseline configs.
- Google SRE Book, ch. 17 "Testing for Reliability" — canonical taxonomy.
- Microsoft Engineering Fundamentals Playbook — gate inventory reference.
- Open Source Security Foundation (OpenSSF) Scorecards — CI gate heuristics.
- 12-factor app (factor XII: Admin processes) — test environments as code.
