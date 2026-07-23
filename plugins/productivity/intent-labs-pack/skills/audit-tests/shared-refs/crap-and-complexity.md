# CRAP & Complexity — Walls 5 and 6

## Contents

[The Formula](#section-1-the-formula) · [Thresholds](#section-2-thresholds) · [Per-Language Tool Matrix](#section-3-per-language-tool-matrix) · [Test-Code CRAP (Wall 6)](#section-4-test-code-crap-wall-6) · [AUDIT Flow](#section-5-audit-flow) · [IMPLEMENT Flow](#section-6-implement-flow) · [Remediation Guidance](#section-7-remediation-guidance) · [Cross-References](#section-8-cross-references) · [Sources](#sources)

CRAP (Change Risk Analyzer and Predictor) combines cyclomatic complexity with
coverage to rank each method by how risky a change to it is. A method that is
complex **and** under-tested is the worst kind of code; CRAP surfaces it.

This reference covers two walls:

- **Wall 5** — CRAP on production code. Gate: no method CRAP > 30; project
  average ≤ 10.

- **Wall 6** — CRAP on test code. Gate: no test method CRAP > 15. Complex
  tests mask bugs and weaken mutation testing.

The skill uses `scripts/crap-score.py` to compute CRAP across languages from
their native complexity and coverage tooling.

---

## Section 1: The Formula

```
CRAP(m) = C(m)^2 * (1 - cov(m)/100)^3 + C(m)
```

Where `C(m)` is the cyclomatic complexity of method `m` and `cov(m)` is its
line coverage as a percentage.

**Two levers for reducing CRAP**:

1. Lower complexity (split the method, extract helpers, use dispatch)
2. Raise coverage (add tests — including negative and boundary tests)

**Only two** — CRAP cannot be reduced by weakening the measurement. Attempts
to do so (lowering coverage floors, marking methods as no-mutate, increasing
the CRAP threshold config) are escape attempts. See
`{baseDir}/scripts/escape-scan.sh`.

---

## Section 2: Thresholds

| CRAP | Band | Action |
|------|------|--------|
| 1–5 | Clean | None |
| 6–15 | Watch | Add tests on next touch |
| 16–30 | Refactor target | Plan to reduce next sprint |
| **>30 (production code)** | **Blocking fail** | Must fix before merge |
| **>15 (test code)** | **Blocking fail** | Split into single-behavior tests |
| Project average **>10** | **Blocking fail** | Systemic refactor required |

Remediation priority (applied automatically by the auto-remediation engine):

1. If complexity > 15 → **refactor first**. Extract methods, replace
   conditionals with polymorphism, split responsibilities. Tests won't
   save a tangled method.

2. If complexity ≤ 15 and coverage < 80% → **tests first**. Add negative
   and boundary tests until coverage crosses 80%, then re-score.

3. If complexity ≤ 5 and coverage ≥ 90% → already clean. Leave alone.

---

## Section 3: Per-Language Tool Matrix

| Language | Complexity | Coverage | Integration |
|----------|-----------|----------|-------------|
| Python | `radon cc -s -a -j` | `coverage json -o coverage.json` | `crap-score.py --lang python` |
| JS/TS | `npx complexity-report --format json` or `js-crap-score` | `c8 --reporter=json` or `jest --coverage --coverageReporters=json` | `crap-score.py --lang js` |
| Java | Crap4j (legacy) or SonarQube | JaCoCo | SonarQube has CRAP widget; Crap4j via maven plugin |
| .NET | NCover (CRAP built-in) or SonarQube | Coverlet | SonarQube Community Edition |
| Ruby | MetricFu (Flog + SimpleCov) | SimpleCov | `metric_fu --out=tmp/metric_fu` |
| Go | `gocyclo -over 15 .` | `go test -coverprofile=c.out -covermode=atomic && go tool cover -func=c.out` | `crap-score.py --lang go` |
| Rust | `rust-code-analysis` (cyclomatic) | `cargo tarpaulin --out Json` | `crap-score.py --lang rust` |
| PHP | PHPMetrics (cyclomatic) | PHPUnit `--coverage-xml` | `crap-score.py --lang php` |

Install per detected language:

```bash
# Python
pip install radon coverage

# JS/TS
npm i -D complexity-report c8

# Go
go install github.com/fzipp/gocyclo/cmd/gocyclo@latest

# Rust
cargo install rust-code-analysis-cli cargo-tarpaulin

# Ruby
gem install metric_fu
```

---

## Section 4: Test-Code CRAP (Wall 6)

The rule: **test methods with CRAP > 15 fail**.

Rationale: a test with complexity > 15 usually:

- Exercises multiple behaviors in one test (violates FIRST's Independent)
- Contains conditional assertion logic (`if cond: assert ... else: assert ...`)
- Loops over generated cases without a Scenario Outline
- Shares setup with logic in ways that obscure what is being asserted

Complex tests also weaken mutation testing: a single test that covers many
paths will kill a mutant that any one of its assertions would catch,
masking the fact that several paths are under-asserted.

**Remediation for complex tests** (the AI must apply):

- Split into one test per behavior.
- Replace if/else in test bodies with separate test methods.
- Replace loops with `@pytest.mark.parametrize` / `it.each` / table tests.
- Move shared setup into fixtures / `beforeEach` / `Background`.

---

## Section 5: AUDIT Flow

```bash
# Unified command — auto-detects language
python scripts/crap-score.py --target both --format both --out reports/crap/

# Output:
#   reports/crap/crap-src.csv        (production methods, sorted desc)
#   reports/crap/crap-test.csv       (test methods, sorted desc)
#   reports/crap/summary.json        (thresholds, averages, pass/fail)
```

### AUDIT report section

```
CRAP & COMPLEXITY (Walls 5 & 6)
  Production code:
    Methods scored:        238
    Max CRAP:              42.1  →  src/billing/invoice.py::calculate_total
    Methods over 30:       2     (BLOCKING)
    Project average:       7.4   (PASS, target ≤ 10)
  Test code:
    Test methods scored:   412
    Max CRAP:              18.7  →  tests/unit/test_invoice.py::test_all_paths
    Tests over 15:         3     (BLOCKING)
  Trend (vs last audit):   +1 blocker, +0.4 avg
```

---

## Section 6: IMPLEMENT Flow

When CRAP tooling is not yet installed, the skill implements Wall 5/6:

### 1. Install tooling (language-detected)

For Python:

```bash
pip install radon coverage
```

### 2. Emit project config

Add to `pyproject.toml`:

```toml
[tool.radon]
exclude = "tests/fixtures/*,migrations/*"
cc_min = "A"

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
fail_under = 80
show_missing = true

[tool.audit-tests.crap]
production_max = 30
production_avg = 10
test_max = 15
```

For JS/TS, add `.c8rc.json`:

```json
{
  "reporter": ["json", "text-summary"],
  "branches": 80,
  "lines": 80,
  "functions": 80,
  "statements": 80
}
```

### 3. Wire a project target

Add to `Makefile`:

```makefile
.PHONY: crap
crap:
  python scripts/crap-score.py --target both --format both --out reports/crap/
  @cat reports/crap/summary.json
```

Or `package.json`:

```json
{
  "scripts": {
    "crap": "node ./scripts/run-crap.js"
  }
}
```

### 4. Copy `crap-score.py` into `scripts/`

So the repo is portable without the skill loaded.

### 5. Wire CI

GitHub Actions snippet:

```yaml
- name: CRAP gate
  run: |
    python scripts/crap-score.py --target both --out reports/crap/
    python -c "import json; s=json.load(open('reports/crap/summary.json')); exit(0 if s['pass'] else 1)"
```

### 6. Initial scan

Run once to establish the baseline. Report any blocking fails to the
engineer; do not commit.

---

## Section 7: Remediation Guidance

When a method fails the CRAP gate, the skill proposes one of:

- **Extract Method** — pull conditional branches or loops into named
  helpers. Each helper gets its own tests.

- **Replace Conditional with Polymorphism** — if/elif chains on a type
  discriminator become subclasses or a dispatch dict.

- **Split by Responsibility** — if the method does I/O *and* business
  logic, split them. Test the logic in isolation.

- **Add boundary tests** — if complexity is ≤ 15 and coverage is the
  problem, generate negative and boundary tests per
  `{baseDir}/references/auto-remediation.md`.

The skill never proposes:

- Raising the CRAP threshold in config
- Adding `# noqa` / pragma bypasses
- Marking the method as `# pragma: no mutate`
- Lowering `fail_under` in `pyproject.toml`

Those are escape attempts and are caught by `scripts/escape-scan.sh`.

---

## Section 8: Cross-References

- Wall 2/3/4 → `{baseDir}/references/test-quality-deep-audit.md`
- Remediation → `{baseDir}/references/auto-remediation.md`
- Escape detection → `{baseDir}/scripts/escape-scan.sh`
- CRAP calculator → `{baseDir}/scripts/crap-score.py`

---

## Sources

- [CRAP Metric — NDepend](https://blog.ndepend.com/crap-metric-thing-tells-risk-code/)
- [Understanding CRAP and Cyclomatic Complexity — OtterWise](https://getotterwise.com/blog/understanding-crap-and-cyclomatic-complexity-metrics)
- [crap4j FAQ (original)](http://www.crap4j.org/faq.html)
- [Clean Code (O'Reilly)](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
