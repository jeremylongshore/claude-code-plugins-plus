# GitHub Audit Engine & Remediation

Triggered by: "audit my tests", "find gaps", "what's missing", "check my repo"

---

## Repository Scan

```bash
# Clone if not local
git clone https://github.com/USER/REPO.git /tmp/audit-REPO
cd /tmp/audit-REPO

# All source files
/usr/bin/find . -type f \( \
  -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
  -o -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.rb" \
  -o -name "*.java" -o -name "*.kt" -o -name "*.php" \
  -o -name "*.cs" -o -name "*.ex" -o -name "*.exs" \
  -o -name "*.swift" -o -name "*.c" -o -name "*.cpp" \
\) -not -path "*/node_modules/*" -not -path "*/.git/*" \
   -not -path "*/vendor/*" -not -path "*/target/*" \
   -not -path "*/dist/*" -not -path "*/build/*" \
   -not -path "*/coverage/*" > /tmp/source-files.txt

# All test files
/usr/bin/find . -type f \( \
  -name "*.test.*" -o -name "*.spec.*" \
  -o -name "*_test.*" -o -name "test_*.py" \
  -o -name "*_spec.rb" \
  -o -name "*Test.java" -o -name "*Tests.java" \
\) -not -path "*/node_modules/*" \
   -not -path "*/.git/*" > /tmp/test-files.txt

echo "Source: $(wc -l < /tmp/source-files.txt) files"
echo "Tests:  $(wc -l < /tmp/test-files.txt) files"
echo "Ratio:  $(echo "scale=1; $(wc -l < /tmp/test-files.txt) * 100 / $(wc -l < /tmp/source-files.txt)" | bc)%"
```

## Gap Mapping

```bash
while IFS= read -r source; do
  base=$(basename "$source" | sed 's/\.[^.]*$//')
  found=$(grep -c "$base" /tmp/test-files.txt 2>/dev/null || echo 0)
  [ "$found" -eq 0 ] && echo "UNTESTED: $source"
done < /tmp/source-files.txt > /tmp/gaps.txt

echo "Untested: $(wc -l < /tmp/gaps.txt) files"
cat /tmp/gaps.txt
```

## CI/CD Audit

```bash
# Check all CI systems
ls .github/workflows/ .circleci/ .buildkite/ \
   .travis.yml .gitlab-ci.yml Jenkinsfile \
   bitbucket-pipelines.yml azure-pipelines.yml 2>/dev/null

# Test step present?
grep -r "test\|vitest\|jest\|pytest\|go test\|rspec\|cargo test\|playwright" \
  .github/workflows/ .circleci/ 2>/dev/null | head -20
```

## Coverage Audit

```bash
# Thresholds enforced?
grep -r "threshold\|branches\|functions\|lines\|coverageThreshold" \
  vitest.config.* jest.config.* .nycrc* 2>/dev/null

# Coverage badge in README?
grep -i "coverage\|codecov\|coveralls" README.md 2>/dev/null
```

## Security Audit

```bash
# Dependency vulnerabilities
pnpm audit --json 2>/dev/null | jq '{
  critical: .metadata.vulnerabilities.critical,
  high: .metadata.vulnerabilities.high,
  moderate: .metadata.vulnerabilities.moderate,
  total: .metadata.vulnerabilities.total
}' 2>/dev/null

# Secrets
gitleaks detect --source=. --report-format=json \
  --report-path=/tmp/secrets.json 2>/dev/null
jq 'length' /tmp/secrets.json 2>/dev/null
```

---

## Console Audit Report

```
═══════════════════════════════════════════════════════
  GITHUB AUDIT REPORT — [REPO NAME]
  Branch: [BRANCH]   Commit: [SHA]
═══════════════════════════════════════════════════════

CODEBASE OVERVIEW
  Source files:    [N]
  Test files:      [N]
  Coverage ratio:  [N]%   (target: >80%)
  Languages:       [detected list]

COVERAGE GAPS
  Untested files:  [N]
  Highest-risk untested:
    [file path] — [why it matters]
    [file path] — [why it matters]
    [file path] — [why it matters]

CI/CD STATUS
  CI configuration present
  Test step in pipeline
  Coverage reporting
  Security scanning
  Lint step
  E2E step

SECURITY
  Secrets exposed:          [N]
  Critical vulnerabilities: [N]
  High:                     [N]
  Moderate:                 [N]

TEST QUALITY SIGNALS
  Coverage thresholds enforced
  E2E tests exist
  API contract tests
  Performance baseline
  Security scanning in CI
  Accessibility tests
  Mutation testing

TEST QUALITY (run Step 7 for full analysis)
  Assertion density:       [X] per test    [Grade]
  Bias patterns detected:  [N]             [Severity]
  Negative test ratio:     [X]%            [Grade]
  Kill rate (if measured): [X]%            [Grade]
  OWASP coverage:          [Grade]
  AI-test risk:            [Level]
  Quality-adjusted cov:    [X]%

REMEDIATION PLAN → See below
═══════════════════════════════════════════════════════
```

---

## TEST_AUDIT.md — Written Deliverable

After the console report, **always generate a markdown file** as the primary deliverable. This is what gets committed, shared, or used as a living document for the team.

Write to: `TEST_AUDIT.md` in the root of the audited repository.

```bash
cat > TEST_AUDIT.md << 'AUDIT'
# Test Audit Report
[generated content — see template below]
AUDIT
```

The document has two mandatory sections and one optional section. Do not skip the strengths section — surfacing what is already working is as important as identifying gaps.

---

### TEST_AUDIT.md Template

```markdown
# Test Audit — [REPO NAME]
> Branch: [BRANCH] · Commit: [SHA] · Audited: [DATE]

---

## What Is Working Well

> This section documents existing test infrastructure that is sound and should be preserved.
> Acknowledge good work — it anchors the team and prevents regression during remediation.

### Coverage & Structure
- [Specific strength found — e.g. "Unit tests cover all service-layer files with consistent
  describe/it structure and clear naming conventions"]
- [e.g. "Test files mirror source directory structure 1:1, making gaps immediately visible"]
- [e.g. "All tests are isolated — no shared mutable state between test cases detected"]
- [e.g. "Coverage is at [X]% line coverage across [N] files — above the 70% baseline threshold"]

### CI/CD Integration
- [e.g. "Test pipeline runs on every pull request with no manual trigger required"]
- [e.g. "Failing tests block merges — the gate is enforced"]
- [e.g. "Test results are cached between runs, reducing average CI time by ~[X]%"]
- [e.g. "Coverage reports are uploaded and tracked per commit via Codecov"]

### Test Quality Signals
- [e.g. "No flaky tests detected across 5 sequential runs"]
- [e.g. "All async tests use proper await patterns — no floating promises"]
- [e.g. "External services are mocked consistently — tests do not hit real APIs"]
- [e.g. "Edge cases are tested alongside happy paths in [N]% of test files"]

### Security & Dependencies
- [e.g. "No exposed secrets found in repository history"]
- [e.g. "Zero critical dependency vulnerabilities — audit is clean"]
- [e.g. "Dependency audit runs in CI — vulnerabilities would block deployment"]

### Documentation & Conventions
- [e.g. "Test naming is human-readable — test failure messages are self-explanatory"]
- [e.g. "README documents how to run the test suite locally"]
- [e.g. "Fixtures and mocks are centralized — not duplicated per test file"]

---

## What Could Be Better

> Each item below identifies a specific gap, explains the concrete risk if it stays unaddressed,
> and describes exactly what to add or change. Sorted by risk — P0 first.
>
> **Note:** If Step 7 (Test Quality Deep Audit) was run, include the "Test Quality Assessment"
> subsection below with bias, mutation, OWASP, and AI-test findings.

### Test Quality Assessment

> This section is populated by Step 7. Include it when quality audit data is available.

#### Assertion Quality
- **Density:** [X] assertions per test ([Grade])
- **Smoke-only assertions:** [N] ([X]% of total) — tests that only check `is not None` or `toBeDefined()`
- **Negative test ratio:** [X]% ([Grade])
- **Boundary test coverage:** [descriptor]

#### Test Bias Analysis
- **Bias patterns detected:** [N] across [M] test files
- **Severity:** [Low/Moderate/High/Critical]
- **Top patterns found:**
  - [Bias type]: [N] instances — [example file:line]
  - [Bias type]: [N] instances — [example file:line]
  - [Bias type]: [N] instances — [example file:line]

#### Mutation Testing Results
- **Kill rate:** [X]% ([Grade])
- **Survivors:** [N] ([N] equivalent, [N] real gaps)
- **Effective coverage:** [X]% (line_coverage × kill_rate)
- **Weakest modules:** [list modules with lowest kill rates]

#### OWASP Security Test Coverage
| Category | Grade | Gap |
|----------|-------|-----|
| A01 Access Control | [Grade] | [what's missing] |
| A03 Injection | [Grade] | [what's missing] |
| A07 Auth Failures | [Grade] | [what's missing] |
| [other categories with gaps] | [Grade] | [what's missing] |

#### AI-Written Test Risk
- **Risk level:** [Low/Moderate/High/Critical]
- **AI-attributed tests:** [N] files ([X]% of test suite)
- **Key concern:** [primary issue found]

---

### P0 — Fix Before Anything Else

#### [Gap Title — e.g. "No tests for authentication middleware"]
**What exists:** [current state — e.g. "src/middleware/auth.ts exists with 340 lines of JWT
validation logic and has zero corresponding test coverage"]

**What is missing:** [specific gap — e.g. "No tests for token expiry, malformed tokens, missing
authorization headers, or role-based access decisions"]

**Why it matters:** [concrete risk — e.g. "Authentication bypass vulnerabilities cannot be caught
before production. A regression here could expose all protected routes to unauthenticated users.
This is the highest-risk untested surface in the codebase."]

**What to add:**
```typescript

// tests/middleware/auth.test.ts
describe('auth middleware', () => {
  it('rejects requests with no token')
  it('rejects expired tokens')
  it('rejects malformed tokens')
  it('allows valid tokens through')
  it('enforces role-based access per route')
})

```

---

#### [Gap Title — e.g. "Exposed secret in commit history"]

**What exists:** [e.g. "API key committed in .env.example at commit abc123 — file was later
deleted but the key persists in git history"]

**What is missing:** [e.g. "Secret rotation + pre-commit hook to prevent recurrence"]

**Why it matters:** [e.g. "Anyone with repository access — including public forks — can retrieve
the key from git history. The key should be rotated immediately regardless of whether it appears
active."]

**What to add:** Rotate the key. Add `gitleaks` as a pre-commit hook and a CI step.

---

### P1 — Core Functionality at Risk

#### [Gap Title — e.g. "No CI pipeline configured"]

**What exists:** [e.g. "Tests can be run locally with `pnpm test` but no `.github/workflows/`
directory exists and no other CI configuration was found"]

**What is missing:** [e.g. "Automated test execution on push and pull request"]

**Why it matters:** [e.g. "Tests only run when a developer remembers to run them. Broken code
can merge to main undetected. The entire value of the existing test suite is contingent on
manual discipline rather than automation."]

**What to add:**

```yaml

# .github/workflows/test.yml

name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v4
      - run: pnpm install --frozen-lockfile
      - run: pnpm test

```

---

#### [Gap Title — e.g. "Coverage below 40% in core domain layer"]

**What exists:** [e.g. "src/domain/ contains [N] files implementing core business rules. Current
line coverage is [X]%."]

**What is missing:** [e.g. "Tests for [list specific files or modules]"]

**Why it matters:** [e.g. "Domain logic is where bugs cause business impact. At [X]% coverage,
the majority of business rule paths are untested. Refactoring or feature changes carry high
regression risk."]

**What to add:** [specific test files and what each should cover]

---

### P2 — Quality and Reliability Gaps

#### [Gap Title — e.g. "No coverage thresholds enforced"]

**What exists:** [e.g. "Coverage is collected via `pnpm test:coverage` but no thresholds are
configured. Coverage can decrease to zero without failing CI."]

**What is missing:** [e.g. "Threshold configuration in vitest.config.ts"]

**Why it matters:** [e.g. "Without enforced thresholds, coverage degrades silently over time.
New features get shipped without tests and the coverage metric becomes meaningless."]

**What to add:**

```typescript

// vitest.config.ts
coverage: {
  thresholds: {
    branches: 70,
    functions: 80,
    lines: 80
  }
}

```

---

#### [Gap Title — e.g. "No E2E tests for critical user flows"]

**What exists:** [e.g. "Unit tests cover individual functions but no browser-level tests exist
for the [login / checkout / onboarding] flows"]

**What is missing:** [e.g. "Playwright test suite covering the paths a real user takes"]

**Why it matters:** [e.g. "Unit tests cannot detect integration failures between the frontend,
API, and database. A user-facing regression can exist even when all unit tests pass. The login
flow has no automated verification at all."]

**What to add:** Playwright suite with tests for [list detected critical flows from the codebase]

---

#### [Gap Title — e.g. "No API contract tests"]

**What exists:** [e.g. "openapi.yaml exists and documents [N] endpoints, but no tests validate
that the running server matches the spec"]

**What is missing:** [e.g. "Contract validation step in CI"]

**Why it matters:** [e.g. "The spec and the implementation can drift without any automated
detection. Consumers of the API build against the spec — a mismatch breaks them silently."]

**What to add:**

```bash

npx dredd openapi.yaml http://localhost:3000

```

Add to CI after server startup step.

---

### P3 — Hardening and Observability

#### Performance Baseline

**What is missing:** Load tests or benchmark assertions for primary endpoints.
**Why it matters:** Performance regressions are invisible without a baseline. A slow endpoint
ships and is only discovered in production under real load.
**What to add:** k6 or Artillery script targeting primary API endpoints with p95 thresholds.

---

#### Accessibility Testing

**What is missing:** Automated WCAG compliance checks.
**Why it matters:** Accessibility failures carry legal risk in many jurisdictions and exclude
real users. axe-core violations are often trivial to fix when caught early and expensive to
remediate after the fact.
**What to add:** axe-core in component tests + `pa11y-ci` in CI against the running app.

---

#### Mutation Testing

**What is missing:** Mutation testing to validate test quality, not just coverage.
**Why it matters:** High coverage can coexist with low-quality tests that never actually
assert correctness. Mutation testing reveals tests that pass regardless of what the code does.
**What to add:** Stryker (JS/TS), mutmut (Python), or PITest (Java) on the core domain layer.

---

#### Visual Regression

**What is missing:** Screenshot comparison against a known-good baseline.
**Why it matters:** UI changes that are visually broken can pass all functional tests. Without
visual regression, layout regressions, style changes, and rendering errors reach production.
**What to add:** Playwright snapshot tests or Chromatic against Storybook components.

---

#### Secret Detection in CI

**What is missing:** Automated secret scanning on every commit.
**Why it matters:** Developers accidentally commit credentials. Without an automated gate,
the only detection is manual review or an incident.
**What to add:** `gitleaks` as a pre-commit hook and a CI step.

---

## Summary Scorecard

| Area | Status | Priority |
|------|--------|----------|
| Unit test coverage | [X]% — [Good / Needs work / Critical] | [P0-P3] |
| Integration tests | [Present / Missing] | [P0-P3] |
| E2E tests | [Present / Missing] | [P0-P3] |
| API contract tests | [Present / Missing] | [P0-P3] |
| CI pipeline | [Configured / Missing] | [P0-P3] |
| Coverage gates | [Enforced / Not enforced] | [P0-P3] |
| Security scanning | [Present / Missing] | [P0-P3] |
| Secret detection | [Clean / Issues found] | [P0-P3] |
| Dependency audit | [Clean / Vulnerabilities] | [P0-P3] |
| Test bias patterns | [N] found — [severity] | [P0-P2] |
| Assertion density | [X] per test — [Grade] | [P1-P3] |
| Negative test ratio | [X]% — [Grade] | [P2-P3] |
| OWASP security coverage | [Grade] overall | [P1-P2] |
| AI-test quality risk | [Level] | [P1-P3] |
| Quality-adjusted coverage | [X]% effective | [P1-P3] |
| Performance baseline | [Present / Missing] | [P3] |
| Accessibility tests | [Present / Missing] | [P3] |
| Mutation testing | [Present / Missing] | [P3] |
| Visual regression | [Present / Missing] | [P3] |

---

*Generated by audit-tests skill · [REPO URL]*

```

After writing `TEST_AUDIT.md`:

```bash
echo "TEST_AUDIT.md written to $(pwd)/TEST_AUDIT.md"
```

Inform the user the file is ready and offer to either commit it to the repo or open it for review.

---

## Remediation Plan

Generated after audit. Sorted by **risk only.**

### Priority Tiers

| Tier | Criteria |
|------|----------|
| P0 Critical | Exposed secrets, auth untested, security vulnerabilities, CI completely broken, kill rate <50%, critical test bias (30+ per 100 tests) |
| P1 High | Core business logic untested, no test pipeline, coverage below 40%, OWASP F-grade categories, AI-test risk High/Critical, assertion density <1.0 |
| P2 Medium | Coverage 40-70%, no E2E, no API contracts, coverage not enforced in CI, kill rate 50-69%, bias 16-30 per 100, negative ratio <10%, OWASP gaps |
| P3 Low | Coverage 70-80%, missing edge cases, no perf baseline, no a11y, kill rate 70-79% (target 85%), density 1.0-1.9, boundary gaps |

### Remediation Plan Output

```
═══════════════════════════════════════════════════════
  REMEDIATION PLAN — [REPO NAME]
═══════════════════════════════════════════════════════

P0 — CRITICAL (fix before anything else)

  [ ] [specific gap description]
      File/Component: [exact location]
      Risk: [what breaks or gets exploited if unfixed]
      Action: [specific thing to do — generate X, add Y, rotate Z]

  [ ] [specific gap description]
      File/Component: [exact location]
      Risk: [concrete consequence]
      Action: [specific action]

P1 — HIGH (core functionality at risk)

  [ ] [specific gap]
      File/Component: [location]
      Risk: [concrete consequence]
      Action: [specific action]

  [ ] [specific gap]
      File/Component: [location]
      Risk: [concrete consequence]
      Action: [specific action]

P2 — MEDIUM (quality and reliability gaps)

  [ ] Enforce coverage thresholds
      Risk: Coverage degrades silently with no gate
      Action: Add to [config file] → branches: 70, functions: 80, lines: 80

  [ ] Add E2E tests for critical user flows
      Risk: UI regressions ship undetected
      Action: Add Playwright tests for [flows detected in codebase]

  [ ] Add API contract tests
      Risk: API drift breaks consumers silently
      Action: Add dredd or Pact against [detected API spec]

P2 — MEDIUM (quality and reliability gaps — continued)

  [ ] Harden test bias patterns
      Bias patterns: [N] detected ([severity])
      Risk: Weak assertions let real bugs survive — coverage number is misleading
      Action: Run Step 8 auto-remediation or manually fix top bias patterns

  [ ] Improve OWASP security test coverage
      Current grade: [X] overall
      Risk: Security-critical paths untested — vulnerabilities ship undetected
      Action: Add auth bypass, injection, access control tests per OWASP checklist

  [ ] Address AI-written test quality
      Risk level: [Level] — [N] AI-attributed test files
      Risk: AI tests tend toward smoke assertions and self-referential checks
      Action: Run mutation testing on AI-tested modules, harden assertions

P3 — LOW (hardening and observability)

  [ ] Add performance baseline
      Action: Add k6 or Artillery script for primary API endpoints

  [ ] Add accessibility tests
      Action: Add axe-core to component tests + Playwright suite

  [ ] Improve mutation kill rate
      Current: [X]% — Target: 85%
      Action: Analyze survivors, add targeted tests for escaped mutants
      See: test-quality-deep-audit.md Section 2 for survivor methodology

  [ ] Increase assertion density
      Current: [X] per test — Target: ≥2.0
      Action: Strengthen smoke-only assertions with exact expected values

  [ ] Add visual regression
      Action: Add Playwright snapshots or Chromatic to Storybook

═══════════════════════════════════════════════════════
ORDER: All P0 before P1. All P1 before P2. P3 is hardening.
═══════════════════════════════════════════════════════
```
