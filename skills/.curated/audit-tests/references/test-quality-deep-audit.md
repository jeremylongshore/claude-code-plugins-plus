# Test Quality Deep Audit

Triggered by: "test quality", "test bias", "mutation testing", "AI tests", "harden tests", "vibe code audit"

This is the deep quality layer that goes beyond coverage percentages. High coverage with weak assertions is worse than moderate coverage with strong assertions — it creates false confidence.

**Cross-references**: this document covers Walls 2–4 (unit tests, coverage, mutation). The remaining walls live in companion references:

- Wall 1 — Acceptance (Gherkin): `{baseDir}/references/acceptance-tests-gherkin.md`
- Walls 5/6 — CRAP on production & test code: `{baseDir}/references/crap-and-complexity.md`
- Wall 7 — Architecture & dependency rules: `{baseDir}/references/architecture-constraints.md`

Escape-attempt detection (test skips, coverage-threshold edits, mutation bypasses, rule-config mutation) is enforced by `{baseDir}/scripts/escape-scan.sh`.

---

## Section 1: Test Bias Detection

AI-written tests (and human tests that copy-paste patterns) develop systematic biases. These biases let mutations survive because the assertions don't actually verify correctness.

### Bias Pattern Scanner

Run these grep patterns against the test directory to detect bias:

```bash
TEST_DIR="tests"  # adjust per project

echo "=== TAUTOLOGICAL ASSERTIONS ==="
# Tests that assert a value equals itself or a trivially derived value
grep -rn "assert.*sorted.*==.*sorted\|assert.*len.*==.*len\|assertEqual.*len.*len" "$TEST_DIR" 2>/dev/null
grep -rn "assert.*==.*str(.*)\|assert.*repr\|assert.*type(.*) ==" "$TEST_DIR" 2>/dev/null

echo "=== SELF-REFERENTIAL ASSERTIONS ==="
# Tests that compute expected value from the same code under test
grep -rn "expected = .*\.\(calculate\|compute\|process\|get\|fetch\|build\)" "$TEST_DIR" 2>/dev/null
grep -rn "assert.*\.count.*==.*len(.*\.items\|\.entries\|\.elements)" "$TEST_DIR" 2>/dev/null

echo "=== SMOKE-ONLY CHECKS ==="
# Tests that only check existence, not correctness
grep -rn "assert .* is not None\b" "$TEST_DIR" 2>/dev/null
grep -rn "assert.*is not None$\|assertIsNotNone\|expect.*toBeDefined()\|expect.*not.*toBeNull()" "$TEST_DIR" 2>/dev/null
grep -rn "assert len(.*).*> 0\|assert len(.*).*>= 1\|expect.*toHaveLength.*expect.*not.*0" "$TEST_DIR" 2>/dev/null
# Count smoke-only vs total assertions
SMOKE=$(grep -rcn "is not None\|assertIsNotNone\|toBeDefined\|not.*toBeNull\|assertNotNone" "$TEST_DIR" 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
TOTAL=$(grep -rcn "assert\|expect(" "$TEST_DIR" 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
echo "Smoke-only: $SMOKE / $TOTAL total assertions ($(echo "scale=1; $SMOKE * 100 / ($TOTAL + 1)" | bc)%)"

echo "=== IDENTITY VS EQUALITY MISUSE ==="
# Using truthiness checks when specific value assertions are needed
grep -rn "assert not .*\|assertFalse(.*)\|expect.*toBeFalsy()" "$TEST_DIR" 2>/dev/null | grep -v "assert not.*raise\|assert not.*call\|assert not.*exist"

echo "=== SYMMETRIC INPUT BIAS ==="
# Tests that use symmetric/degenerate inputs that don't exercise edge cases
grep -rn "(0, 0)\|(1, 1)\|(100, 100)\|(0.0, 0.0)" "$TEST_DIR" 2>/dev/null
grep -rn "\"test\"\|'test'\|\"foo\"\|'foo'\|\"bar\"\|'bar'\|\"abc\"\|'abc'" "$TEST_DIR" 2>/dev/null | head -20

echo "=== RANGE-ONLY ASSERTIONS ==="
# Tests that check ranges instead of exact values
grep -rn "assert.*<=.*<=\|assert.*>=.*and.*<=\|assert.*in range\|assertBetween\|toBeGreaterThan.*toBeLessThan" "$TEST_DIR" 2>/dev/null

echo "=== MUTATION-INSENSITIVE STRING CHECKS ==="
# Tests that check substring presence rather than exact output
grep -rn 'assert.*" in \|assert.*in str(\|assertIn.*"\|expect.*toContain(' "$TEST_DIR" 2>/dev/null | grep -v "import\|from\|#"
```

### Bias Scoring

Count total bias pattern matches and score:

| Bias Matches (per 100 tests) | Grade | Action |
|------|-------|--------|
| 0–5 | Low | No action needed |
| 6–15 | Moderate | Review flagged tests, harden weakest |
| 16–30 | High | Systematic remediation needed — run Step 8 |
| 30+ | Critical | Test suite provides false confidence — full rewrite of flagged tests |

```bash
# Quick bias score calculator
BIAS_COUNT=0
for pattern in "is not None$" "assertIsNotNone" "toBeDefined()" \
               "sorted.*==.*sorted" "len.*==.*len" \
               "(0, 0)" "(1, 1)" "(100, 100)" \
               "assert.*<=.*<=" 'assert.*" in '; do
  COUNT=$(grep -rn "$pattern" "$TEST_DIR" 2>/dev/null | wc -l)
  BIAS_COUNT=$((BIAS_COUNT + COUNT))
done
TEST_COUNT=$(grep -rn "def test_\|it('\|it(\"\\|test('\|test(\"" "$TEST_DIR" 2>/dev/null | wc -l)
echo "Bias patterns: $BIAS_COUNT across $TEST_COUNT tests"
echo "Per-100 rate: $(echo "scale=1; $BIAS_COUNT * 100 / ($TEST_COUNT + 1)" | bc)"
```

---

## Section 2: Mutation Testing Setup & Interpretation

Mutation testing is the gold standard for test quality. It modifies source code (creates "mutants") and checks if tests catch the change. A surviving mutant means your tests don't actually verify that behavior.

### Python — mutmut v3

**Important:** mutmut v3 has breaking changes from v2. The CLI is different.

```toml
# pyproject.toml
[tool.mutmut]
paths_to_mutate = ["src/"]
tests_dir = "tests/"
runner = "python -m pytest -x -q --tb=no"
# also_copy — critical for projects with non-Python files needed at test time
also_copy = ["fixtures/", "*.json", "*.yaml"]
```

**Running mutmut v3:**

```bash
# Full run (slow — run on CI or overnight)
mutmut run

# Target specific modules (recommended for iterative work)
mutmut run --paths-to-mutate src/core/validators.py
mutmut run --paths-to-mutate src/core/

# View results
mutmut results

# Show a specific survivor
mutmut show <id>

# HTML report
mutmut html
open html/index.html
```

**v3 vs v2 gotchas:**

- v3 uses `mutmut run` not `mutmut run --paths-to-mutate` (path is positional in some versions)
- v3 stores results in `.mutmut-cache/` (SQLite), not a flat file
- `mutmut results` output format changed — parse carefully
- `also_copy` is critical — without it, tests that need fixtures/configs will fail (false killed)
- Use `--runner` to customize — default may not match your test command

### JavaScript/TypeScript — Stryker

```json
// stryker.conf.json
{
  "$schema": "https://raw.githubusercontent.com/stryker-mutator/stryker4s/master/stryker-schema.json",
  "mutate": ["src/**/*.ts", "!src/**/*.test.ts", "!src/**/*.d.ts"],
  "testRunner": "vitest",
  "reporters": ["html", "clear-text", "progress"],
  "coverageAnalysis": "perTest",
  "thresholds": { "high": 80, "low": 60, "break": 50 }
}
```

```bash
npx stryker run
npx stryker run --mutate "src/services/**/*.ts"  # target specific modules
```

### Java — PITest

```groovy
// build.gradle
plugins { id 'info.solidsoft.pitest' version '1.15.0' }
pitest {
    targetClasses = ['com.example.core.*']
    targetTests = ['com.example.core.*Test']
    mutators = ['DEFAULTS']
    outputFormats = ['HTML']
    timestampedReports = false
    mutationThreshold = 70
}
```

```bash
./gradlew pitest
```

### Rust — cargo-mutants

```bash
cargo install cargo-mutants
cargo mutants                           # full run
cargo mutants --file src/core.rs        # target specific file
cargo mutants -- --test-threads=1       # reduce parallelism if flaky
```

### Kill Rate Benchmarks

| Kill Rate | Grade | Interpretation |
|-----------|-------|----------------|
| 90–100% | S | Exceptional — tests catch nearly every possible bug |
| 80–89% | A | Strong — suitable for production-critical code |
| 70–79% | B | Good — acceptable for most codebases |
| 60–69% | C | Adequate — room for improvement in core modules |
| 50–59% | D | Weak — tests miss many real bugs |
| 40–49% | E | Poor — tests provide little confidence |
| <40% | F | Failing — tests are decoration, not verification |

**Quality-adjusted coverage formula:**

```
effective_coverage = line_coverage × kill_rate
```

Example: 90% line coverage × 65% kill rate = 58.5% effective coverage (D grade)

### Equivalent Mutant Patterns

Not all surviving mutants are test gaps. Some are **equivalent mutants** — changes that don't affect observable behavior:

- Replacing `x < y` with `x <= y` when `x == y` is impossible by domain constraint
- Changing `return list(items)` to `return list(reversed(reversed(items)))` — same result
- Boundary changes in pure logging/formatting code
- Changes to unreachable code paths

**Rule of thumb:** If you can't write a test that distinguishes the mutant from the original, it's equivalent. Mark it and move on.

### Survivor Analysis Methodology

For each surviving mutant:

1. **Read the mutation** — what was changed? (operator swap, constant change, removed line)
2. **Find the test** — is there a test that exercises this code path?
3. **Check the assertion** — does the test assert the specific behavior that changed?
4. **Classify:**
   - **Missing test** — no test covers this path → write one
   - **Weak assertion** — test covers path but doesn't check the right thing → strengthen
   - **Equivalent mutant** — change doesn't affect behavior → mark as equivalent
   - **Test infrastructure gap** — test exists but can't detect the change due to mocking → restructure

### When to Run Mutation Testing

| Situation | Scope | Frequency |
|-----------|-------|-----------|
| Pre-release | Core domain modules only | Every release |
| After major refactor | Changed modules | Once after stabilization |
| Audit / quality check | Full codebase | On demand |
| CI (advanced) | Changed files only | Every PR (if fast enough) |
| New module | New module's tests | Before merge |

---

## Section 3: Assertion Quality Scoring

### Assertion Density

Assertions per test function — a core quality metric.

```bash
# Python
TEST_FUNCS=$(grep -rn "def test_" "$TEST_DIR" 2>/dev/null | wc -l)
ASSERTIONS=$(grep -rn "assert\b\|assertEqual\|assertRaises\|assertIn\|assertIs\|assertTrue\|assertFalse\|assertAlmostEqual\|assertGreater\|assertLess\|pytest.raises\|pytest.warns" "$TEST_DIR" 2>/dev/null | wc -l)
echo "Assertion density: $(echo "scale=2; $ASSERTIONS / ($TEST_FUNCS + 1)" | bc) per test"

# JavaScript/TypeScript
TEST_FUNCS=$(grep -rn "it('\|it(\"\\|test('\|test(\"" "$TEST_DIR" 2>/dev/null | wc -l)
ASSERTIONS=$(grep -rn "expect(\|assert\.\|should\." "$TEST_DIR" 2>/dev/null | wc -l)
echo "Assertion density: $(echo "scale=2; $ASSERTIONS / ($TEST_FUNCS + 1)" | bc) per test"

# Go
TEST_FUNCS=$(grep -rn "func Test" "$TEST_DIR" 2>/dev/null | wc -l)
ASSERTIONS=$(grep -rn "assert\.\|require\.\|t\.Error\|t\.Fatal\|t\.Fail" "$TEST_DIR" 2>/dev/null | wc -l)
echo "Assertion density: $(echo "scale=2; $ASSERTIONS / ($TEST_FUNCS + 1)" | bc) per test"
```

| Density | Grade | Interpretation |
|---------|-------|----------------|
| ≥3.0 | Excellent | Thorough multi-aspect verification |
| 2.0–2.9 | Good | Solid coverage of behavior |
| 1.5–1.9 | Adequate | Minimum acceptable |
| 1.0–1.4 | Weak | Most tests check only one thing superficially |
| <1.0 | Critical | Many tests have no assertions (smoke tests) |

### Negative Test Ratio

Tests that verify error handling, rejection, and invalid input paths.

```bash
# Python
NEGATIVE=$(grep -rn "pytest.raises\|assertRaises\|with.*raises\|assert.*Error\|assert.*Exception\|assert.*Invalid\|assert.*error\|assert.*fail\|assert.*reject" "$TEST_DIR" 2>/dev/null | wc -l)
echo "Negative tests: $NEGATIVE / $TEST_FUNCS ($(echo "scale=1; $NEGATIVE * 100 / ($TEST_FUNCS + 1)" | bc)%)"

# JavaScript/TypeScript
NEGATIVE=$(grep -rn "toThrow\|rejects\|toHaveBeenCalledWith.*Error\|expect.*error\|expect.*null\|expect.*undefined\|catch\|rejected" "$TEST_DIR" 2>/dev/null | wc -l)
echo "Negative tests: $NEGATIVE / $TEST_FUNCS ($(echo "scale=1; $NEGATIVE * 100 / ($TEST_FUNCS + 1)" | bc)%)"
```

| Negative Ratio | Grade | Interpretation |
|----------------|-------|----------------|
| ≥25% | Excellent | Error paths well-covered |
| 15–24% | Good | Reasonable error coverage |
| 10–14% | Adequate | Some gaps in error handling |
| 5–9% | Weak | Most error paths untested |
| <5% | Critical | Almost no error path testing |

### Boundary Test Detection

Tests that exercise edge cases and boundaries.

```bash
# Look for boundary values
grep -rn "\b0\b.*assert\|assert.*\b0\b\|\b-1\b.*assert\|assert.*\b-1\b" "$TEST_DIR" 2>/dev/null | wc -l
grep -rn "empty\|blank\|nil\|null\|None\|undefined\|NaN\|Infinity\|MAX_\|MIN_\|INT_MAX\|overflow\|underflow" "$TEST_DIR" 2>/dev/null | wc -l
grep -rn '"".*assert\|assert.*""\|assert.*\[\]\|assert.*{}' "$TEST_DIR" 2>/dev/null | wc -l
echo "Boundary indicators found — review for adequacy"
```

| Boundary Signals | Grade |
|-----------------|-------|
| ≥1 per test file | Good |
| Some files, not all | Adequate |
| Rare or absent | Weak — add boundary tests |

### Test Isolation Score

Tests should not depend on execution order or shared mutable state.

```bash
# Global/module-level mutable state in test files
echo "=== SHARED MUTABLE STATE ==="
grep -rn "^[a-zA-Z_].*= \[\]\|^[a-zA-Z_].*= {}\|^[a-zA-Z_].*= set()" "$TEST_DIR" 2>/dev/null
grep -rn "global \|setattr\|monkeypatch.*setenv" "$TEST_DIR" 2>/dev/null

# File I/O without cleanup
echo "=== FILE I/O WITHOUT TMP ==="
grep -rn "open(.*'w'\|with open\|write(" "$TEST_DIR" 2>/dev/null | grep -v "tmp\|temp\|fixture\|mock"

# Database state
echo "=== DATABASE MUTATIONS ==="
grep -rn "\.create(\|\.save(\|\.delete(\|\.update(" "$TEST_DIR" 2>/dev/null | grep -v "mock\|fake\|stub\|fixture"
```

---

## Section 4: Security Test Coverage (OWASP Top 10)

For each OWASP category, check if tests exist that cover the attack surface.

### A01: Broken Access Control

```bash
grep -rn "unauthorized\|forbidden\|403\|401\|access.denied\|permission\|role.*check\|rbac\|acl\|can_access\|is_authorized" "$TEST_DIR" 2>/dev/null
```

**Should test:**

- [ ] Unauthenticated access to protected endpoints returns 401
- [ ] Wrong role/permission returns 403
- [ ] Horizontal privilege escalation (user A can't access user B's data)
- [ ] Vertical privilege escalation (regular user can't access admin endpoints)
- [ ] CORS configuration rejects unauthorized origins

### A02: Cryptographic Failures

```bash
grep -rn "encrypt\|decrypt\|hash\|bcrypt\|argon\|scrypt\|hmac\|jwt\|token.*valid\|certificate\|tls\|ssl" "$TEST_DIR" 2>/dev/null
```

**Should test:**

- [ ] Passwords are hashed (not stored in plaintext)
- [ ] Tokens expire and are rejected after expiry
- [ ] Sensitive data is not logged or returned in error responses

### A03: Injection

```bash
grep -rn "injection\|sql.*inject\|xss\|sanitize\|escape\|parameterized\|prepared.*statement\|html.*encode\|script.*tag" "$TEST_DIR" 2>/dev/null
```

**Should test:**

- [ ] SQL injection payloads are rejected or parameterized
- [ ] XSS payloads in input are sanitized
- [ ] Command injection via user input is blocked
- [ ] Path traversal (`../`) in file paths is rejected

### A04: Insecure Design

```bash
grep -rn "rate.limit\|throttle\|brute.force\|lockout\|captcha\|anti.automation" "$TEST_DIR" 2>/dev/null
```

**Should test:**

- [ ] Rate limiting enforced on auth endpoints
- [ ] Account lockout after failed attempts
- [ ] Business logic abuse scenarios

### A05: Security Misconfiguration

```bash
grep -rn "header.*security\|content.security.policy\|csp\|x.frame\|hsts\|x.content.type\|cors\|debug.*false\|debug.*off" "$TEST_DIR" 2>/dev/null
```

**Should test:**

- [ ] Security headers present (CSP, HSTS, X-Frame-Options)
- [ ] Debug mode disabled in production config
- [ ] Default credentials not accepted
- [ ] Error responses don't leak stack traces

### A06: Vulnerable Components

```bash
grep -rn "audit\|vulnerability\|cve\|advisory\|outdated\|deprecated" "$TEST_DIR" 2>/dev/null
```

**Should test:**

- [ ] Dependency audit runs in CI (pnpm audit, pip-audit, etc.)
- [ ] Known vulnerable versions are blocked

### A07: Authentication Failures

```bash
grep -rn "login\|logout\|auth\|session\|password\|credential\|mfa\|2fa\|otp\|reset.*password\|forgot.*password" "$TEST_DIR" 2>/dev/null
```

**Should test:**

- [ ] Login with valid credentials succeeds
- [ ] Login with invalid credentials fails with generic message
- [ ] Session expires after timeout
- [ ] Password reset flow works and old password is invalidated
- [ ] Brute force protection on login

### A08: Software and Data Integrity

```bash
grep -rn "checksum\|integrity\|signature\|verify.*sign\|webhook.*valid\|csrf\|anti.forgery" "$TEST_DIR" 2>/dev/null
```

**Should test:**

- [ ] CSRF tokens required for state-changing operations
- [ ] Webhook signatures verified before processing
- [ ] File upload integrity checks

### A09: Logging & Monitoring Failures

```bash
grep -rn "audit.*log\|security.*log\|log.*auth\|log.*fail\|log.*access\|monitoring\|alert" "$TEST_DIR" 2>/dev/null
```

**Should test:**

- [ ] Failed auth attempts are logged
- [ ] Sensitive data is NOT in logs
- [ ] Security events trigger alerts

### A10: Server-Side Request Forgery (SSRF)

```bash
grep -rn "ssrf\|url.*valid\|allowlist\|blocklist\|internal.*url\|localhost.*block\|127\.0\.0\.1.*block\|metadata.*block" "$TEST_DIR" 2>/dev/null
```

**Should test:**

- [ ] User-supplied URLs are validated against allowlist
- [ ] Internal/private IP ranges are blocked
- [ ] Cloud metadata endpoints (169.254.169.254) are blocked

### OWASP Coverage Scoring

| Category | Tests Found | Checklist Items Covered | Grade |
|----------|-------------|------------------------|-------|
| A01 Access Control | [N] | [X/5] | [A-F] |
| A02 Crypto | [N] | [X/3] | [A-F] |
| A03 Injection | [N] | [X/4] | [A-F] |
| A04 Insecure Design | [N] | [X/3] | [A-F] |
| A05 Misconfig | [N] | [X/4] | [A-F] |
| A06 Vulnerable Deps | [N] | [X/2] | [A-F] |
| A07 Auth Failures | [N] | [X/5] | [A-F] |
| A08 Integrity | [N] | [X/3] | [A-F] |
| A09 Logging | [N] | [X/3] | [A-F] |
| A10 SSRF | [N] | [X/3] | [A-F] |
| **Overall** | | | **[A-F]** |

Grading: A = ≥80% items covered, B = 60–79%, C = 40–59%, D = 20–39%, F = <20%

---

## Section 5: AI-Written Test Detection

AI-generated tests (from Copilot, ChatGPT, Claude, vibe coding sessions) have characteristic patterns. They're not inherently bad, but they need extra scrutiny because they tend to:

- Test what the code does rather than what it should do
- Use generic placeholder values
- Have high structural similarity
- Lack domain-specific edge cases

### Commit-Based Detection

```bash
# Bulk test additions (50+ lines of test code in a single commit)
git log --all --numstat --format="%H %s" -- "tests/" "*test*" "*spec*" | \
  awk '/^[0-9]/ {added+=$1} /^[a-f0-9]{40}/ {if(added>50) print prev, added; added=0; prev=$0}' | \
  head -20

# Co-author tags indicating AI assistance
git log --all --format="%H %s%n%b" | grep -B1 -i "co-authored-by.*claude\|co-authored-by.*copilot\|co-authored-by.*chatgpt\|co-authored-by.*cursor\|generated\|auto-generated\|ai-generated"
```

### Pattern-Based Detection

```bash
echo "=== GENERIC TEST NAMES ==="
# AI often generates test_function_name or test_module_basic patterns
grep -rn "def test_.*_basic\|def test_.*_works\|def test_.*_success\|def test_.*_returns" "$TEST_DIR" 2>/dev/null | head -20

echo "=== TEMPLATE STRUCTURE ==="
# Identical setUp/tearDown patterns repeated across files
grep -rn "def setUp\|def setup_method\|beforeEach\|beforeAll" "$TEST_DIR" 2>/dev/null | \
  awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -10

echo "=== VERBOSE DOCSTRINGS ==="
# AI loves adding docstrings to every test — humans rarely do
grep -rn '"""Test that\|"""Verify that\|"""Check that\|"""Ensure that' "$TEST_DIR" 2>/dev/null | wc -l

echo "=== SUSPICIOUSLY UNIFORM STRUCTURE ==="
# Count test functions per file — AI tends to generate uniform counts
grep -rn "def test_" "$TEST_DIR" 2>/dev/null | awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -20
```

### AI-Test Scrutiny Protocol

When AI-written tests are detected:

1. **Don't delete them** — they're a starting point, not garbage
2. **Check assertion quality** — AI tests typically have low assertion density and high smoke-only ratio
3. **Check for tautologies** — AI often asserts `result == function(input)` which is self-referential
4. **Check input diversity** — AI tends to use `"test"`, `"foo"`, `123`, `True` — not domain-specific values
5. **Run mutation testing** on the AI-tested modules — this is the definitive quality check
6. **Harden, don't rewrite** — replace weak assertions with specific expected values, add boundary cases

### AI-Test Risk Score

| Indicator | Points |
|-----------|--------|
| Bulk commit (50+ test lines) | +2 |
| Co-author AI tag present | +3 |
| Generic test names (>30%) | +2 |
| Verbose docstrings (>50% of tests) | +1 |
| Uniform tests-per-file count | +1 |
| Low assertion density (<1.5) | +2 |
| High smoke-only ratio (>20%) | +2 |

| Total Points | Risk Level | Action |
|-------------|------------|--------|
| 0–3 | Low | Standard review |
| 4–6 | Moderate | Run mutation testing on these modules |
| 7–9 | High | Deep review + mutation testing + hardening |
| 10+ | Critical | Treat as scaffolding — systematic hardening required |

---

## Section 6: Test Quality Scorecard

After running all checks, compile the scorecard:

```
═══════════════════════════════════════════════════════
  TEST QUALITY SCORECARD — [REPO NAME]
═══════════════════════════════════════════════════════

ASSERTION QUALITY
  Density:            [X] per test     [Grade]
  Smoke-only ratio:   [X]%             [Grade]
  Negative test ratio: [X]%            [Grade]
  Boundary coverage:  [descriptor]     [Grade]

MUTATION TESTING
  Kill rate:          [X]%             [Grade]
  Survivors:          [N]
  Equivalent:         [N]
  Effective coverage: [X]%  (line_coverage × kill_rate)

SECURITY COVERAGE (OWASP Top 10)
  A01 Access Control: [Grade]
  A02 Crypto:         [Grade]
  A03 Injection:      [Grade]
  A04 Insecure Design:[Grade]
  A05 Misconfig:      [Grade]
  A06 Vulnerable Deps:[Grade]
  A07 Auth Failures:  [Grade]
  A08 Integrity:      [Grade]
  A09 Logging:        [Grade]
  A10 SSRF:           [Grade]
  Overall:            [Grade]

TEST ISOLATION
  Shared mutable state: [N files]      [Clean / Warning]
  File I/O without tmp: [N instances]  [Clean / Warning]
  DB mutations:         [N instances]  [Clean / Warning]

AI-TEST RISK
  Risk score:         [N] points       [Level]
  AI-attributed tests: [N] files
  Recommended action: [action]

TEST BIAS
  Bias patterns found: [N]
  Per-100-tests rate:  [X]
  Severity:            [Low/Moderate/High/Critical]
  Top bias types:      [list top 3]

QUALITY-ADJUSTED COVERAGE
  Line coverage:       [X]%
  Kill rate:           [X]%
  Effective coverage:  [X]% = [line]% × [kill]%
  Grade:               [S/A/B/C/D/E/F]
═══════════════════════════════════════════════════════
```

---

## Section 7: Integration with TEST_AUDIT.md

When running as part of a full audit (Step 5 → Step 7), append the quality findings to the TEST_AUDIT.md deliverable.

### Where to Insert

Add a new subsection under "What Could Be Better" in TEST_AUDIT.md:

```markdown
### Test Quality Assessment

#### Assertion Quality
- **Density:** [X] assertions per test ([Grade])
- **Smoke-only assertions:** [N] ([X]% of total) — [tests that only check `is not None` or `toBeDefined()`]
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
| [categories with gaps] | [grade] | [what's missing] |

#### AI-Written Test Risk
- **Risk level:** [Low/Moderate/High/Critical]
- **AI-attributed tests:** [N] files ([X]% of test suite)
- **Key concern:** [primary issue found]
```

### Summary Scorecard Additions

Add these rows to the existing Summary Scorecard table in TEST_AUDIT.md:

```markdown
| Test bias patterns | [N] found — [severity] | [P0-P3] |
| Assertion density | [X] per test — [Grade] | [P2-P3] |
| Negative test ratio | [X]% — [Grade] | [P2-P3] |
| OWASP security coverage | [Grade] overall | [P1-P2] |
| AI-test quality risk | [Level] | [P1-P3] |
| Quality-adjusted coverage | [X]% effective | [P1-P3] |
```

### Remediation Plan Integration

Quality findings map to remediation tiers:

| Finding | Tier |
|---------|------|
| Kill rate <50% | P0 — tests provide false confidence |
| Critical bias (30+ per 100 tests) | P0 — systematic assertion failure |
| OWASP category at F grade (security-critical app) | P1 |
| AI-test risk High or Critical | P1 |
| Assertion density <1.0 | P1 |
| Kill rate 50–69% | P2 |
| Bias 16–30 per 100 tests | P2 |
| Negative ratio <10% | P2 |
| OWASP gaps in non-critical categories | P2 |
| Kill rate 70–79% (target 85%) | P3 |
| Density 1.0–1.9 | P3 |
| Boundary coverage gaps | P3 |
