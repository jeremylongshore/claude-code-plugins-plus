# 7-Layer Testing Taxonomy (Canonical)

The 7-layer pyramid is the authoritative map of what a repository's testing system can include. Layers are ordered cheapest→most expensive to run and from closest-to-developer to closest-to-user. Each layer has distinct failure modes; the walls (acceptance, unit, coverage, mutation, CRAP, architecture) sit *inside* layers, not alongside them.

`audit-tests` classifies a repo, maps applicable layers per `layer-applicability.md`, and checks presence / configuration / enforcement for each. `implement-tests` installs missing layers per the playbooks in `implement-tests/references/install-playbooks/`.

---

## Layer 1 — Git Hooks & CI Enforcement

Stops bad changes before they land in the repo or propagate to CI.

| Concern | Tools | Gate |
|---|---|---|
| Pre-commit hooks | Husky, lefthook, pre-commit.com, core.hooksPath | Installed; runs on `pre-commit` |
| Staged-file filters | lint-staged, pre-commit filter | Only touches staged paths |
| Commit-message policy | commitlint, Conventional Commits, gitlint | `commit-msg` hook; CI lint |
| Pre-push hooks | Husky `pre-push`, lefthook `pre-push` | Runs unit + lint before push |
| CI pipeline | GH Actions, GitLab CI, CircleCI, Jenkins, Buildkite, Azure Pipelines | On PR + merge; required checks enforced |
| Branch protection | GH branch protection, GitLab protected branches | Required reviews, status checks, signed commits |

Deep reference: `shared-refs/hooks-and-ci.md`.

---

## Layer 2 — Static Analysis & Linting

No code execution — reads source and config. Fastest feedback, highest signal-to-noise on style and common defects.

| Concern | Tools (examples) |
|---|---|
| Linting | ESLint, Ruff, Flake8, golangci-lint, Clippy, RuboCop, PHPStan, Psalm, Checkstyle, ShellCheck, hadolint |
| Formatting | Prettier, Black, gofmt, rustfmt, dotnet format, clang-format |
| Type checking | tsc, mypy, pyright, Sorbet, Flow |
| Complexity | radon, gocyclo, rust-code-analysis (feeds `crap-score.py`) |
| Secret scanning | gitleaks, trufflehog, detect-secrets |
| Dependency vuln scan | npm audit, pip-audit, cargo audit, govulncheck, bundler-audit, Trivy |
| Container image scan | Trivy, Grype, Syft (SBOM) |
| IaC scan | Checkov, tfsec, kubescape, kube-bench |
| **Doc lint** | **markdownlint-cli2, markdownlint, remark-lint** |
| **Prose lint** | **Vale (banned terms, anti-slop, house style), proselint, write-good, alex** |
| **Link integrity** | **lychee, markdown-link-check, hyperlink** |
| **Doc formatting** | **Prettier (Markdown table + code-fence formatting — distinct from code formatting), dprint** |
| **Frontmatter / schema validation** | **JSON-Schema-driven custom validators (e.g. `validate-skillmd`, `validate-plugin`, `validate-agent`), js-yaml, ajv-cli, gray-matter** |

Deep references: `shared-refs/linters-formatters-types.md`, `shared-refs/security-testing.md`.

**Gap additions vs raw user taxonomy:**

- Container scanning and IaC scanning are separated from "dependency scanning" — different tool ecosystems, different findings.
- **Doc & Prose Quality is a first-class L2 concern**, not "below the line." Repos that ship documentation (specs, blueprints, marketplace listings, partner deliverables, SKILL.md corpora) MUST gate doc quality at L2; the failure mode of a broken link in a partner deliverable or a banned-term leak in a public spec is as material as a lint error in source. The 5 doc rows above are evaluated by `/audit-tests` whenever the repo has `>= 50` markdown files OR a `000-docs/` directory OR an `agentskills.io`-style SKILL.md corpus.

---

## Layer 3 — Unit & Function

Covers the core TDD cycle. Walls 2–6 live here.

| Concern | Tools |
|---|---|
| Unit test framework | Vitest, Jest, Mocha, Pytest, unittest, `go test`, `cargo test`, RSpec, JUnit, PHPUnit, ExUnit, xUnit |
| Architecture / fitness functions | dependency-cruiser, import-linter, ArchUnit, deptrac, arch-go |
| Property-based testing | Hypothesis, fast-check, proptest, jqwik, ScalaCheck, StreamData, FsCheck |
| Fuzzing | libFuzzer, AFL++, cargo-fuzz, `go test -fuzz`, Atheris, Jazzer, OSS-Fuzz |
| Mutation testing | mutmut, Stryker, PITest, cargo-mutants, Infection |
| Coverage | coverage.py, c8, JaCoCo, tarpaulin, go cover, SimpleCov |
| CRAP / complexity gate | `audit-tests/scripts/crap-score.py` |
| Memory safety | Valgrind, AddressSanitizer, MemorySanitizer, ThreadSanitizer |
| Flakiness gate | `pytest --count=3`, Jest `--testPathPattern ... --runInBand --ci` + retry |

Deep references: `shared-refs/frameworks.md`, `shared-refs/crap-and-complexity.md`, `shared-refs/architecture-constraints.md`, `shared-refs/property-and-fuzz.md`, `test-quality-deep-audit.md`.

**Gap additions vs raw user taxonomy:**

- **Fuzzing separated from property-based.** PBT proves invariants; fuzzing finds crashers. Both needed for adversarial repos.
- **Flakiness gate** is an explicit measurable threshold (e.g., "0 flaky tests over 3 reruns"), not a note.
- **Per-module mutation floors** — certain hot modules (payments, auth) carry stricter kill-rate targets set in `tests/TESTING.md`.

---

## Layer 4 — Integration & Regression

Covers unit interactions with real external systems (DB, message queue, storage) and cross-version stability.

| Concern | Tools |
|---|---|
| Integration fixtures | Testcontainers (per-language bindings), pytest-docker, dockertest (Go) |
| API / service contract | Dredd, Schemathesis, RestAssured |
| Consumer-driven contracts | Pact (consumer/provider), Spring Cloud Contract |
| Migration testing | Flyway, Liquibase, Alembic, Prisma Migrate, Atlas, Bytebase |
| Database integration | testcontainers-postgres/mysql/mongo, pg-tap, tSQLt |
| Fake services | WireMock, Mountebank, MockServer |
| Message-queue integration | Kafka TestContainers, Redis TestContainers, Localstack |
| Regression snapshot | Jest snapshots, approvaltests, insta (Rust) |
| IaC integration tests | Terratest, InSpec, Ansible Molecule, kitchen-terraform |
| Kubernetes manifest tests | kubeconform, kube-score, polaris, kube-bench, Kyverno |
| **Doc-framework build** | **MDX (`@mdx-js/mdx`), Astro (`astro check`), Docusaurus (`docusaurus build`), Next.js content (`next build`), Hugo (`hugo --gc --minify`), Jekyll (`bundle exec jekyll build`) — gates that docs *render* not just lint** |

Deep references: `shared-refs/integration-and-infra.md`, `shared-refs/specialized-testing.md`.

**Gap additions vs raw user taxonomy:**

- **Migration testing** separated out — a broken migration in prod is unrecoverable; a missing unit test is not.
- **Contract testing (Pact)** separated from plain "API testing" — different discipline (bidirectional), different artifacts (pact files), different CI.

---

## Layer 5 — System Quality

Non-functional requirements: performance, security, accessibility, compatibility, resilience.

| Concern | Tools |
|---|---|
| Performance / load | k6, Locust, Artillery, Gatling, wrk, JMeter |
| Security — SAST | Semgrep, CodeQL, Bandit, Brakeman, gosec |
| Security — DAST | OWASP ZAP, Burp Suite, Nuclei |
| Accessibility | axe-core, pa11y, Lighthouse, WAVE |
| Browser compatibility | BrowserStack, Sauce Labs, Playwright multi-browser |
| Mobile compatibility | Appium, Detox, XCUITest, Espresso |
| Chaos engineering | Chaos Mesh, Litmus, Gremlin, Pumba, Toxiproxy, AWS FIS |

Deep references: `shared-refs/security-testing.md`, `shared-refs/specialized-testing.md`, `shared-refs/property-and-fuzz.md` § Chaos.

**Gap additions vs raw user taxonomy:**

- **Chaos engineering** separated from load/perf — a service can survive load and still fail under a partition.

**Demotions:**

- **Usability testing** moves out of the audited pyramid. It cannot be automated and is covered informationally in `philosophy.md`.

---

## Layer 6 — E2E & BDD / Gherkin

User-facing, through the full stack.

| Concern | Tools |
|---|---|
| End-to-end web | Playwright, Cypress, WebdriverIO, Selenium |
| End-to-end API | Postman + Newman, Karate, Bruno |
| Smoke / critical-path | Playwright `@smoke`, `cypress-cloud` tagged suites |
| Visual regression | Percy, Chromatic, Playwright/Cypress screenshot diff, Lost Pixel |
| BDD runners (Wall 1 glue) | Cucumber, behave, godog, Reqnroll, FitNesse, ExecutableSpec |

Deep references: `shared-refs/e2e-testing.md`, `shared-refs/acceptance-tests-gherkin.md`.

**Gap additions vs raw user taxonomy:**

- **Visual regression** separated from snapshot (L4) — snapshot diffs data shape; visual regression diffs rendered pixels. Both needed for UI repos.

---

## Layer 7 — Acceptance & Business Validation

Does the delivered thing solve the stated problem?

| Concern | Tools / Artifacts |
|---|---|
| UAT (stakeholder-run) | TestRail, Xray, manual checklists |
| Automated acceptance | Cucumber, SpecFlow/Reqnroll, FitNesse tying `.feature` to real user journeys |
| Business-rules validation | Drools, Camunda DMN |

Deep reference: `shared-refs/acceptance-tests-gherkin.md`.

**Demotions:**

- **Exploratory testing** moves out of the audited pyramid (cannot automate); documented informationally in `philosophy.md`.

---

## Walls inside layers

The walls from v6.0.0 (acceptance / unit / coverage / mutation / CRAP-prod / CRAP-test / architecture) are all *invariants* enforced at specific layers:

| Wall | Layer | Enforcement |
|---|---|---|
| Wall 1 — Acceptance (Gherkin) | L7 (spec) + L6 (glue) | Hash-pinned `.feature`; `gherkin-lint.sh`; BDD runner returns 0 |
| Wall 2 — Unit tests | L3 | 0 failing, 0 unauthorized skips |
| Wall 3 — Coverage floor | L3 | Line/branch ≥ policy floor in `TESTING.md` |
| Wall 4 — Mutation kill-rate | L3 | ≥ 70% (or per-module floor) |
| Wall 5 — CRAP on prod code | L3 | No method > 30; avg ≤ 10 |
| Wall 6 — CRAP on test code | L3 | No test method > 15 |
| Wall 7 — Architecture rules | L3 (fitness fns) | 0 violations; rule configs hash-pinned |

The walls didn't go away; they live *inside* L3 (walls 2–7) and L6/L7 (wall 1). The taxonomy adds five more layers (L1, L2, L4, L5, L6-E2E-specific) that the walls don't individually cover.

---

## How this taxonomy is used

- **Audit:** `taxonomy-mapper-agent` reads the repo classification from `tests/TESTING.md` (or computes it via `test-discovery-agent` on first run), then for each applicable layer checks presence / config / CI wiring / enforcement.
- **Implement:** `scaffold-architect-agent` reads the gap list and picks install order across layers; `framework-installer-agent` executes per-playbook installs from `install-playbooks/L{1..7}-*.md`.
- **Report:** `TEST_AUDIT.md` (transient) and `tests/TESTING.md` (durable) both use L1–L7 as their canonical structure.
