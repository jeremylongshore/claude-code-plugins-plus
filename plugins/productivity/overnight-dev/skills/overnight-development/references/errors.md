# Overnight Development - Error Handling Reference

## Git Hook Failures

### Pre-commit Hook: Tests Not Passing

**Symptom:** Commit is rejected with "tests must pass before committing."

**Cause:** One or more unit tests failed during the pre-commit hook execution.

**Resolution:**

```bash
# Run tests manually to see failures
npm test -- --verbose 2>&1 | head -50

# Run only failing test file
npm test -- --testPathPattern="failing-test.spec.ts"

# If test is flaky, check for timing issues
npm test -- --detectOpenHandles --forceExit
```

### Pre-push Hook: Coverage Threshold Not Met

**Symptom:** Push rejected with "coverage below threshold."

**Resolution:**

```bash
# Check current coverage
npm test -- --coverage --coverageReporters=text-summary

# Find uncovered lines
npm test -- --coverage --coverageReporters=text | grep -E "^(Stmts|Branch|Funcs|Lines)"

# Generate detailed HTML report
npm test -- --coverage --coverageReporters=html
open coverage/index.html
```

## TDD Enforcement Errors

### Missing Test File for New Source File

**Symptom:** Hook rejects commit because `src/feature.ts` exists without corresponding `tests/feature.spec.ts`.

**Resolution:**

```bash
# Create the test file with a basic structure
cat > tests/feature.spec.ts << 'EOF'
import { describe, it, expect } from 'vitest';
import { myFunction } from '../src/feature';

describe('feature', () => {
  it('should handle the base case', () => {
    expect(myFunction()).toBeDefined();
  });

  it('should handle edge cases', () => {
    expect(() => myFunction(null)).not.toThrow();
  });
});
EOF
```

### Test-to-Code Ratio Below Minimum

**Symptom:** "Test-to-code ratio is 0.3, minimum is 0.5."

**Resolution:** Add more tests to cover untested paths. Focus on:

- Error handling branches
- Edge cases (empty input, null, boundary values)
- Integration paths between modules

## Runtime Errors

### Process Terminated Mid-Run (OOM)

**Symptom:** Overnight process exits with signal 9 (SIGKILL) or "JavaScript heap out of memory."

**Resolution:**

```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"

# Run with memory monitoring
node --expose-gc --trace-gc overnight-runner.js 2>gc.log &
```

### File System Permissions

**Symptom:** "EACCES: permission denied" during file write operations.

**Resolution:**

```bash
# Check file ownership
ls -la .git/hooks/

# Ensure hooks are executable
chmod +x .git/hooks/pre-commit .git/hooks/pre-push

# Fix ownership if running as different user
sudo chown -R $(whoami) .git/
```

### Lock File Conflicts

**Symptom:** "Another git process seems to be running" or stale lock files after crash.

**Resolution:**

```bash
# Remove stale lock
rm -f .git/index.lock

# Check for zombie processes
ps aux | grep git | grep -v grep

# Kill stuck processes
pkill -f "git commit"
```

## Recovery Procedures

### Recovering from Incomplete Overnight Run

```bash
# Check what was accomplished
git log --oneline --since="yesterday 11pm"

# Review uncommitted changes
git diff --stat
git stash list

# Resume from last checkpoint
git stash pop  # if work was stashed
npm test       # verify current state
```

### Rolling Back a Bad Overnight Session

```bash
# Find the commit before the session started
git log --oneline -20

# Soft reset to preserve changes for review
git reset --soft COMMIT_HASH

# Or hard reset to discard everything
git reset --hard COMMIT_HASH
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
