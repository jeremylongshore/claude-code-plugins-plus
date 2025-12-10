# CI Test Execution - Quick Reference Guide

**Date:** 2025-12-10
**Status:** Active in CI pipeline

---

## For Plugin Developers

### Before Submitting a PR

Run these commands locally to catch issues before CI:

```bash
# For MCP plugins (TypeScript/Node.js)
cd plugins/mcp/your-plugin/
pnpm install
pnpm build          # Must pass
pnpm test           # Must pass
pnpm typecheck      # Must pass
pnpm lint           # Must pass

# From repository root
./scripts/validate-all-plugins.sh plugins/mcp/your-plugin/
```

### Adding Tests to Your Plugin

#### MCP Plugin (TypeScript)

1. Create test file:
```bash
mkdir -p plugins/mcp/your-plugin/tests/
touch plugins/mcp/your-plugin/tests/your-feature.test.ts
```

2. Add test scripts to package.json:
```json
{
  "scripts": {
    "test": "vitest",
    "test:ci": "vitest run"
  },
  "devDependencies": {
    "vitest": "^4.0.8"
  }
}
```

3. Create vitest.config.ts:
```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
  },
});
```

4. Write tests:
```typescript
import { describe, it, expect } from 'vitest';
import { yourFunction } from '../src/your-module';

describe('yourFunction', () => {
  it('should do something', () => {
    const result = yourFunction('input');
    expect(result).toBe('expected');
  });
});
```

---

## CI Pipeline Flow

```
PR/Push → validate job (existing)
            ↓ (pass)
         test job (new)
            ├─ mcp-plugins (parallel)
            ├─ python-tests (parallel)
            └─ validation-scripts (parallel)
            ↓ (all pass)
         ✅ Merge allowed
```

---

## Test Job Details

### 1. MCP Plugins Test Matrix

**When:** Always runs for MCP plugin changes
**Runtime:** ~3-5 minutes
**Parallel:** Yes (with other matrices)

**Steps:**
1. Setup Node.js 20 + pnpm 8
2. `pnpm install --frozen-lockfile`
3. `pnpm build` (all MCP plugins)
4. For each plugin with test script:
   - `pnpm test:ci` (or `pnpm test -- --run`)
5. `pnpm typecheck` (all MCP plugins)
6. `pnpm lint` (all MCP plugins)

**Failure Triggers:**
- Build error
- Test failure
- Type error
- Linting issue

### 2. Python Tests Matrix

**When:** Always runs (ready for future Python tests)
**Runtime:** ~2 minutes
**Parallel:** Yes

**Steps:**
1. Setup Python 3.12
2. Install pytest, pytest-cov, pytest-asyncio
3. Find test files (test_*.py, *_test.py)
4. Run pytest with coverage
5. Upload coverage to Codecov

**Current Status:**
- No test files found (framework ready)
- Non-blocking until tests added

### 3. Validation Scripts Matrix

**When:** Always runs
**Runtime:** ~2 minutes
**Parallel:** Yes

**Steps:**
1. Test validate-all-plugins.sh on sample plugin
2. Run validate-skills-schema.py (185 skills)
3. Run validate-frontmatter.py (253 plugins)

**Purpose:**
- Ensures validation scripts work correctly
- Catches regressions in validation logic

---

## Common CI Failures

### Build Failure

```
Error: Running TypeScript build...
src/index.ts:10:5 - error TS2322: Type 'string' is not assignable to type 'number'.
```

**Fix:**
```bash
cd plugins/mcp/your-plugin/
pnpm typecheck  # Reproduce locally
# Fix type errors
pnpm build      # Verify fix
```

### Test Failure

```
FAIL tests/feature.test.ts
  ✕ should calculate correctly (5ms)
    Expected: 10
    Received: 12
```

**Fix:**
```bash
cd plugins/mcp/your-plugin/
pnpm test       # Reproduce locally
# Fix logic or test
pnpm test       # Verify fix
```

### Lint Failure

```
/plugins/mcp/your-plugin/src/index.ts
  12:5  error  'unused' is defined but never used  no-unused-vars
```

**Fix:**
```bash
cd plugins/mcp/your-plugin/
pnpm lint       # Reproduce locally
# Remove unused variable
pnpm lint       # Verify fix
```

### Type Check Failure

```
src/server.ts:45:7 - error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
```

**Fix:**
```bash
cd plugins/mcp/your-plugin/
pnpm typecheck  # Reproduce locally
# Fix type annotation
pnpm typecheck  # Verify fix
```

---

## Local Testing Checklist

Before pushing to GitHub, run this checklist:

```bash
# 1. Install dependencies
pnpm install

# 2. Build
pnpm build
# ✅ No build errors

# 3. Run tests
pnpm test
# ✅ All tests pass

# 4. Type checking
pnpm typecheck
# ✅ No type errors

# 5. Linting
pnpm lint
# ✅ No lint errors

# 6. Validate plugin structure
./scripts/validate-all-plugins.sh plugins/mcp/your-plugin/
# ✅ All validations pass

# 7. Check for hardcoded secrets
grep -r "api_key\|password\|secret" plugins/mcp/your-plugin/src/
# ✅ No secrets found (or only placeholders)
```

---

## Debugging CI Failures

### View Test Logs

1. Go to GitHub Actions tab
2. Click failed workflow run
3. Click "test" job
4. Expand failed matrix (e.g., "mcp-plugins")
5. Read error output

### Reproduce Locally

```bash
# Clone the exact commit that failed
git checkout <commit-sha>

# For MCP plugins
cd plugins/mcp/your-plugin/
pnpm install --frozen-lockfile  # Same as CI
pnpm build
pnpm test:ci

# For validation scripts
./scripts/validate-all-plugins.sh plugins/mcp/your-plugin/
```

### Check Dependencies

```bash
# Verify pnpm-lock.yaml is committed
git status pnpm-lock.yaml

# Verify package.json versions match lock file
pnpm install --frozen-lockfile
```

---

## CI Performance

### Average Runtimes

- **validate job:** 2-3 minutes
- **mcp-plugins matrix:** 3-5 minutes
- **python-tests matrix:** 2 minutes
- **validation-scripts matrix:** 2 minutes

**Total CI time:** ~5-7 minutes (parallel execution)

### Optimization Tips

1. Keep tests fast (< 1s per test)
2. Use `test:ci` script for CI-optimized runs
3. Avoid slow integration tests in CI (use E2E separately)
4. Cache dependencies (handled by GitHub Actions)

---

## Test Coverage

### Current Coverage

| Plugin | Tests | Type Check | Lint |
|--------|-------|------------|------|
| project-health-auditor | ✅ | ✅ | ✅ |
| conversational-api-debugger | ✅ | ✅ | ✅ |
| domain-memory-agent | ✅ | ✅ | ✅ |
| design-to-code | ⚠️ | ✅ | ✅ |
| workflow-orchestrator | ⚠️ | ✅ | ✅ |
| ai-experiment-logger | ⚠️ | ✅ | ✅ |

⚠️ = No tests yet (non-blocking, but should be added)

### Coverage Goals

- **Target:** 65% code coverage minimum
- **Current:** Not yet measured (coverage reporting ready)
- **Next step:** Add coverage thresholds to CI

---

## FAQ

### Q: My plugin doesn't have tests yet. Will CI fail?

**A:** No. The CI checks if a test script exists. If not, it shows a warning but doesn't fail. However, you should add tests before production use.

### Q: Can I skip tests temporarily?

**A:** No. Tests are mandatory once they exist. If a test is failing, fix the test or the code, don't skip it.

### Q: How do I run only type checking without tests?

**A:** `pnpm typecheck` runs only TypeScript compiler, no tests.

### Q: What if my plugin uses a different test framework?

**A:** The CI checks for a `test` or `test:ci` script in package.json. You can use any test framework (Jest, Mocha, etc.) as long as the script exists and exits with code 0 on success.

### Q: Can I disable linting for specific files?

**A:** Yes, using ESLint ignore comments or .eslintignore, but use sparingly. Fix issues rather than ignoring them.

### Q: How do I add Python tests?

**A:** Create test files matching `test_*.py` or `*_test.py` patterns. The CI will automatically discover and run them with pytest.

---

## Related Documentation

- **Full Report:** `/home/jeremy/000-projects/claude-code-plugins/claudes-docs/CI-TEST-EXECUTION-ENHANCEMENT.md`
- **Workflow File:** `/home/jeremy/000-projects/claude-code-plugins/.github/workflows/validate-plugins.yml`
- **Contributing Guide:** `/home/jeremy/000-projects/claude-code-plugins/CONTRIBUTING.md`
- **Security Policy:** `/home/jeremy/000-projects/claude-code-plugins/SECURITY.md`

---

## Support

If you encounter CI issues:

1. Check GitHub Actions logs for specific error
2. Reproduce locally using checklist above
3. Search existing issues: https://github.com/jeremylongshore/claude-code-plugins/issues
4. Open new issue with CI logs and local reproduction steps

---

**Last Updated:** 2025-12-10
**Status:** Active in production CI
