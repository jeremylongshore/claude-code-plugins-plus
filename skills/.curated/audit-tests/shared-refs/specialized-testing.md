# Specialized Testing

API, performance, security, accessibility, type safety, visual regression, and mutation testing.

---

## API & Contract Testing

### REST

```bash
# Supertest (Node — runs inline with your unit test runner)
pnpm vitest run tests/api/
# or: npx jest tests/api/

# curl
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health

# httpie
http GET :3000/api/health
http POST :3000/api/resource key=value

# Newman (Postman collections)
npx newman run collection.json -e env.json

# Bruno CLI
npx @usebruno/cli run collection/ --env local
```

### OpenAPI Contract Validation

```bash
npx swagger-cli validate openapi.yaml
npx @redocly/cli lint openapi.yaml
npx dredd openapi.yaml http://localhost:3000
schemathesis run openapi.yaml --url http://localhost:3000    # fuzz from spec
```

### Consumer-Driven Contracts (Pact)

```bash
pnpm test:pact
pnpm run pact:publish
pnpm run pact:verify
```

### GraphQL

```bash
npx graphql-inspector validate schema.graphql
npx graphql-inspector diff old.graphql new.graphql
pnpm vitest run tests/graphql/
```

### gRPC

```bash
grpcurl -plaintext localhost:50051 list
grpcurl -plaintext -d '{}' localhost:50051 pkg.Service/Method
ghz --insecure --proto service.proto \
    --call pkg.Service/Method \
    --concurrency 10 --total 1000 localhost:50051
```

---

## Performance & Load Testing

### k6

```bash
k6 run tests/load/api.js
k6 run --out json=results.json tests/load/api.js
k6 run --vus 50 --duration 30s tests/load/api.js
```

### Artillery

```bash
npx artillery run tests/load/artillery.yml
npx artillery run --output report.json tests/load/artillery.yml
npx artillery report report.json
```

### Locust (Python)

```bash
locust -f tests/load/locustfile.py --headless \
  -u 100 -r 10 --host http://localhost:3000
```

### Lighthouse (Web Performance)

```bash
npx lighthouse http://localhost:3000 \
  --output=json --output-path=lighthouse.json
npx lhci autorun
```

### Apache Bench (Quick Baseline)

```bash
ab -n 1000 -c 50 http://localhost:3000/api/endpoint
```

### Vitest Bench (Microbenchmarks)

```bash
pnpm vitest bench
```

---

## Security Testing

### Dependency Audit

```bash
pnpm audit                # Node
pip-audit                 # Python
bundle audit              # Ruby
govulncheck ./...         # Go
cargo audit               # Rust
./gradlew dependencyCheckAnalyze  # Java
```

### SAST (Static Analysis)

```bash
semgrep --config=p/security-audit .
semgrep --config=p/javascript .
bandit -r src/ -ll                       # Python
gosec ./...                              # Go
```

### Secret Detection

```bash
gitleaks detect --source=. --verbose
gitleaks detect --source=. --log-opts="--all"   # full history
trufflehog git file://. --only-verified
detect-secrets scan > .secrets.baseline
detect-secrets audit .secrets.baseline
```

### Dynamic Scanning (DAST)

```bash
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:3000 -r zap-report.html
docker run -t owasp/zap2docker-stable zap-full-scan.py \
  -t http://localhost:3000 -r zap-full-report.html
```

### Container & Infrastructure

```bash
trivy image myapp:latest
trivy fs .
trivy repo https://github.com/org/repo
grype myapp:latest
checkov -d .                       # IaC: Terraform, K8s, Dockerfile
```

---

## Accessibility Testing

### axe-core (Component Level)

```ts
import { axe } from 'jest-axe'

it('has no accessibility violations', async () => {
  const { container } = render(<Component />)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})
```

### Playwright + axe (Full Page)

```ts
import AxeBuilder from '@axe-core/playwright'

test('page has no violations', async ({ page }) => {
  await page.goto('/dashboard')
  const results = await new AxeBuilder({ page }).analyze()
  expect(results.violations).toEqual([])
})
```

### Pa11y

```bash
npx pa11y http://localhost:3000
npx pa11y http://localhost:3000 --standard WCAG2AA
npx pa11y-ci --sitemap http://localhost:3000/sitemap.xml
```

### Lighthouse Accessibility

```bash
npx lighthouse http://localhost:3000 \
  --only-categories=accessibility \
  --output=json | jq '.categories.accessibility.score'
```

---

## Type Safety & Schema Testing

```bash
npx tsc --noEmit                   # TypeScript
buf lint                           # Protobuf
buf breaking --against .git#branch=main
npx @redocly/cli lint openapi.yaml # OpenAPI
npx ajv validate -s schema.json -d data.json  # JSON Schema
```

---

## Visual Regression

### Playwright Snapshots

```ts
await expect(page).toHaveScreenshot('page.png', { maxDiffPixelRatio: 0.02 })
```

```bash
npx playwright test --update-snapshots
```

### Percy

```bash
npx percy exec -- npx playwright test
npx percy exec -- npx cypress run
```

### Chromatic (Storybook)

```bash
npx chromatic --project-token=<TOKEN>
```

### BackstopJS

```bash
npx backstop test
npx backstop approve
```

---

## Mutation Testing

Validates that tests actually catch bugs — not just that they pass. High coverage with low kill rate means tests confirm behavior exists but don't verify it's correct.

For full mutation testing configuration, interpretation, and survivor analysis methodology, see `{baseDir}/references/test-quality-deep-audit.md` Section 2.

### Quick Start by Language

```bash
# JavaScript / TypeScript (Stryker)
npx stryker run
npx stryker run --mutate "src/core/**/*.ts"    # target specific modules

# Python (mutmut v3)
mutmut run
mutmut run --paths-to-mutate src/core/
mutmut results
mutmut show <id>
mutmut html                                     # HTML report

# Java (PITest)
./gradlew pitest

# Rust (cargo-mutants)
cargo install cargo-mutants
cargo mutants
cargo mutants --file src/core.rs
```

### Configuration

**Python (pyproject.toml):**

```toml
[tool.mutmut]
paths_to_mutate = ["src/"]
tests_dir = "tests/"
runner = "python -m pytest -x -q --tb=no"
also_copy = ["fixtures/", "*.json", "*.yaml"]   # critical for non-Python test deps
```

**JavaScript/TypeScript (stryker.conf.json):**

```json
{
  "mutate": ["src/**/*.ts", "!src/**/*.test.ts", "!src/**/*.d.ts"],
  "testRunner": "vitest",
  "reporters": ["html", "clear-text", "progress"],
  "coverageAnalysis": "perTest",
  "thresholds": { "high": 80, "low": 60, "break": 50 }
}
```

### Kill Rate Benchmarks

| Kill Rate | Grade | Interpretation |
|-----------|-------|----------------|
| 90–100% | S | Exceptional |
| 80–89% | A | Strong — production-critical quality |
| 70–79% | B | Good — acceptable for most codebases |
| 60–69% | C | Adequate — core modules need hardening |
| 50–59% | D | Weak — tests miss many real bugs |
| <50% | F | Failing — tests are decoration |

**Quality-adjusted coverage:** `effective_coverage = line_coverage × kill_rate`

### When to Run

| Situation | Scope | Frequency |
|-----------|-------|-----------|
| Pre-release | Core domain modules | Every release |
| After major refactor | Changed modules | Once |
| Audit / quality check | Full codebase | On demand |
| New module | New module's tests | Before merge |

### Security Test Coverage Audit

When auditing a codebase, check whether security-critical behaviors are actually tested. For the full OWASP Top 10 test coverage audit with grep patterns and checklists, see `{baseDir}/references/test-quality-deep-audit.md` Section 4.

Quick check — do security tests exist at all?

```bash
# Auth/access control tests
grep -rn "unauthorized\|forbidden\|403\|401\|access.denied\|permission" tests/ 2>/dev/null | wc -l

# Injection tests
grep -rn "injection\|sanitize\|escape\|xss\|parameterized" tests/ 2>/dev/null | wc -l

# Session/token tests
grep -rn "expired\|invalid.*token\|session.*timeout\|jwt" tests/ 2>/dev/null | wc -l

echo "If any count is 0, run Step 7 for full OWASP assessment"
```
