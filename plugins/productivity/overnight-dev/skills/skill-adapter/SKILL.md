---
name: overnight-dev-autonomous-sessions
description: |
  Comprehensive autonomous development skill for running 6-8 hour overnight coding sessions with enforced test-driven development through Git hooks.
  Activates when: setting up overnight development, configuring TDD workflows, running autonomous sessions, debugging test failures iteratively, enforcing code quality through hooks.
  Transforms "should work" into "does work" by continuously iterating until all tests pass.
license: MIT
allowed-tools: [Bash, Read, Write, Edit, Grep, Glob, TodoWrite]
metadata:
  author: "Intent Solutions IO"
  version: "1.0.0"
  category: "productivity"
  keywords: ["overnight", "autonomous", "TDD", "testing", "git hooks", "continuous development"]
---

# Overnight Development Autonomous Sessions

Comprehensive skill for running fully autonomous 6-8 hour development sessions where Claude works continuously until all tests pass, features are complete, and production-ready code is delivered.

## Core Philosophy

**"Don't stop until it's green."**

The overnight development methodology enforces quality through Git hooks that block commits until all tests pass. This creates a forcing function where broken code cannot be committed, requiring Claude to iterate, debug, and fix until success is achieved. No human intervention needed - just clear goals and morning brings fully tested features.

## Workflow

### Phase 1: Environment Assessment and Setup Validation

To prepare for overnight development, first assess the project environment to ensure autonomous operation is viable.

#### 1.1 Verify Prerequisites

Check that essential infrastructure exists:

```bash
# Verify Git repository
git status

# Check for test framework
ls package.json pytest.ini Cargo.toml go.mod  # One must exist

# Verify at least one test exists
npm test 2>/dev/null || pytest --co 2>/dev/null || cargo test --list 2>/dev/null || go test -list . ./... 2>/dev/null

# Check for linter configuration
ls .eslintrc* .flake8 clippy.toml .golangci.yml
```

If any prerequisites are missing, establish them before proceeding:

```bash
# Initialize Git if needed
git init

# Create minimal test if none exists
cat > test/sample.test.js << 'EOF'
describe('Sample Test', () => {
  it('should pass', () => {
    expect(true).toBe(true);
  });
});
EOF
```

#### 1.2 Deploy Overnight Development Hooks

Install Git hooks using bundled setup script:

```bash
# Execute setup script
./scripts/setup-overnight-hooks.sh

# Alternatively, manual installation:
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Overnight Dev: Pre-commit hook
echo "🚀 Overnight Dev: Running pre-commit checks..."

# Load configuration
CONFIG_FILE=".overnight-dev.json"
if [ -f "$CONFIG_FILE" ]; then
    TEST_CMD=$(jq -r '.testCommand // "npm test"' "$CONFIG_FILE")
    LINT_CMD=$(jq -r '.lintCommand // "npm run lint"' "$CONFIG_FILE")
    AUTO_FIX=$(jq -r '.autoFix // false' "$CONFIG_FILE")
    MIN_COVERAGE=$(jq -r '.minCoverage // 0' "$CONFIG_FILE")
else
    TEST_CMD="npm test"
    LINT_CMD="npm run lint"
    AUTO_FIX=false
    MIN_COVERAGE=0
fi

# Run linting
echo "📝 Running linting..."
if [ "$AUTO_FIX" = "true" ]; then
    $LINT_CMD --fix
else
    $LINT_CMD
fi

if [ $? -ne 0 ]; then
    echo "❌ Linting failed. Fix errors and try again."
    exit 1
fi

# Run tests
echo "🧪 Running tests..."
$TEST_CMD

if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Fix failing tests and try again."
    exit 1
fi

echo "✅ All checks passed!"
exit 0
EOF

chmod +x .git/hooks/pre-commit
```

#### 1.3 Configure for Technology Stack

Create `.overnight-dev.json` configuration tailored to the project:

```json
{
  "testCommand": "npm test -- --coverage --watchAll=false",
  "lintCommand": "npm run lint",
  "requireCoverage": true,
  "minCoverage": 80,
  "autoFix": true,
  "maxAttempts": 50,
  "stopOnMorning": true,
  "morningHour": 7,
  "logFile": ".overnight-dev-log.txt",
  "commitInterval": 10,
  "debugMode": false
}
```

For different stacks, adjust commands accordingly:

**Python Projects:**
```json
{
  "testCommand": "pytest --cov=. --cov-report=term-missing -v",
  "lintCommand": "flake8 . && black --check .",
  "autoFix": false,
  "minCoverage": 85
}
```

**Rust Projects:**
```json
{
  "testCommand": "cargo test --all-features",
  "lintCommand": "cargo clippy -- -D warnings",
  "autoFix": false,
  "minCoverage": 0
}
```

### Phase 2: Task Definition and Success Criteria

To ensure successful autonomous operation, establish clear, testable goals with objective success criteria.

#### 2.1 Structure the Overnight Task

Define tasks using the SMART framework:

```markdown
## Overnight Task Definition

**Task:** Implement JWT authentication with refresh tokens
**Duration:** 6-8 hours autonomous operation

### Success Criteria
✓ All authentication tests passing (0 failures)
✓ Test coverage ≥ 90% for auth module
✓ Integration tests for login/logout/refresh flows
✓ No security vulnerabilities in dependency scan
✓ API documentation generated
✓ Clean commit history with conventional commits

### Constraints
- Use existing database schema
- Follow project code style guide
- Maintain backward compatibility
- No external service dependencies
```

#### 2.2 Create Test Specification First

Before implementation, define comprehensive test suite:

```javascript
// test/auth.test.js
describe('JWT Authentication', () => {
  describe('User Login', () => {
    it('should return JWT token for valid credentials');
    it('should reject invalid credentials with 401');
    it('should rate limit after 5 failed attempts');
    it('should log security events');
  });

  describe('Token Refresh', () => {
    it('should issue new access token with valid refresh token');
    it('should reject expired refresh tokens');
    it('should maintain user session continuity');
  });

  describe('Token Validation', () => {
    it('should validate JWT signature');
    it('should reject expired tokens');
    it('should extract user claims correctly');
  });

  describe('Logout', () => {
    it('should invalidate refresh token');
    it('should clear session data');
    it('should log logout event');
  });
});
```

### Phase 3: Test-Driven Development Cycle

Execute TDD methodology with continuous iteration until all tests pass.

#### 3.1 Implement Red-Green-Refactor Cycle

Follow strict TDD discipline:

```bash
# Step 1: Write failing test (RED)
cat > test/auth/login.test.js << 'EOF'
describe('Login', () => {
  it('should return JWT for valid credentials', async () => {
    const result = await login('user@example.com', 'password123');
    expect(result.token).toBeDefined();
    expect(result.expiresIn).toBe(3600);
  });
});
EOF

# Step 2: Run test to confirm failure
npm test -- test/auth/login.test.js
# Expected: Test fails because login() doesn't exist

# Step 3: Write minimal implementation (GREEN)
cat > src/auth/login.js << 'EOF'
async function login(email, password) {
  // Minimal implementation to pass test
  if (email === 'user@example.com' && password === 'password123') {
    return {
      token: 'jwt-token-here',
      expiresIn: 3600
    };
  }
  throw new Error('Invalid credentials');
}
module.exports = { login };
EOF

# Step 4: Run test to confirm pass
npm test -- test/auth/login.test.js
# Expected: Test passes

# Step 5: Refactor with confidence (REFACTOR)
# Improve implementation while keeping tests green
```

#### 3.2 Handle Test Failures Systematically

When tests fail, apply debugging protocol:

```markdown
## Debugging Protocol for Failed Tests

### Step 1: Analyze Failure
- Read complete error message
- Identify specific assertion that failed
- Note expected vs actual values
- Check stack trace for error location

### Step 2: Form Hypothesis
Based on error analysis, identify likely cause:
- [ ] Logic error in implementation
- [ ] Incorrect test setup/teardown
- [ ] Missing edge case handling
- [ ] Async timing issue
- [ ] External dependency problem

### Step 3: Investigate
Add targeted logging to understand flow:
```javascript
console.log('DEBUG: Input values:', { email, password });
console.log('DEBUG: User lookup result:', user);
console.log('DEBUG: Token generation input:', payload);
```

### Step 4: Fix Specifically
Make minimal change addressing root cause:
```javascript
// Before (failing):
const user = await User.findOne({ email });

// After (passing):
const user = await User.findOne({ email: email.toLowerCase() });
```

### Step 5: Verify Fix
- Run specific failing test
- Run full test suite
- Check coverage didn't decrease
- Ensure no regressions

### Step 6: Clean Up
- Remove debug logging
- Add test for discovered edge case
- Document lesson learned
```

### Phase 4: Continuous Quality Enforcement

Maintain code quality throughout the overnight session using automated checks.

#### 4.1 Commit Discipline with Hooks

Every commit attempt triggers quality gates:

```bash
# Attempting commit triggers pre-commit hook
git add src/auth/login.js test/auth/login.test.js
git commit -m "feat(auth): implement JWT login with email/password"

# Hook runs automatically:
# 🚀 Overnight Dev: Running pre-commit checks...
# 📝 Running linting...
# ✅ Linting passed
# 🧪 Running tests...
# ✅ All tests passed (47/47)
# ✅ Coverage: 94%
# [main abc123] feat(auth): implement JWT login
```

If commit fails, iterate until success:

```bash
# ❌ Tests failed (45/47 passing)
# Review failure → Fix code → Try commit again
# Repeat until all tests pass
```

#### 4.2 Track Progress Continuously

Monitor session progress through structured logging:

```bash
# Initialize progress log
cat > .overnight-dev-log.txt << 'EOF'
OVERNIGHT DEVELOPMENT SESSION
=============================
Started: $(date)
Goal: JWT Authentication Implementation
Success Criteria: 100% tests passing, 90% coverage

PROGRESS LOG
------------
EOF

# Log each significant event
echo "[$(date +%H:%M)] Initial setup complete - 12/12 tests passing" >> .overnight-dev-log.txt
echo "[$(date +%H:%M)] Added login endpoint - 15/18 tests passing" >> .overnight-dev-log.txt
echo "[$(date +%H:%M)] Debugging token validation - 17/18 tests passing" >> .overnight-dev-log.txt
echo "[$(date +%H:%M)] All tests passing - 24/24 tests, 92% coverage" >> .overnight-dev-log.txt
```

### Phase 5: Iterative Debugging and Problem Resolution

When encountering persistent failures, apply systematic debugging strategies.

#### 5.1 Common Failure Patterns and Solutions

**Pattern: Async Test Timeouts**
```javascript
// Problem: Test times out
it('should validate token', async () => {
  const result = validateToken(token); // Missing await!
  expect(result.valid).toBe(true);
});

// Solution: Properly await async operations
it('should validate token', async () => {
  const result = await validateToken(token);
  expect(result.valid).toBe(true);
});
```

**Pattern: State Pollution Between Tests**
```javascript
// Problem: Tests pass individually but fail together
// Solution: Proper setup/teardown
beforeEach(() => {
  // Reset database state
  jest.clearAllMocks();
  // Clear in-memory caches
  tokenCache.clear();
});

afterEach(async () => {
  // Clean up test data
  await User.deleteMany({ email: /test@/ });
});
```

**Pattern: Environment-Specific Failures**
```javascript
// Problem: Works locally, fails in CI
// Solution: Explicit environment configuration
const config = {
  jwtSecret: process.env.JWT_SECRET || 'test-secret-do-not-use',
  tokenExpiry: process.env.TOKEN_EXPIRY || '1h',
  isDevelopment: process.env.NODE_ENV !== 'production'
};
```

#### 5.2 Advanced Debugging Techniques

For complex issues, employ advanced strategies:

```bash
# Binary search for breaking commit
git bisect start
git bisect bad HEAD
git bisect good abc123  # Last known good commit
# Run tests at each step until finding breaking change

# Isolated test execution
npm test -- --testNamePattern="should validate JWT signature" --verbose

# Coverage gap analysis
npm test -- --coverage --coverageReporters=html
# Open coverage/index.html to see uncovered lines

# Dependency conflict resolution
npm ls  # Check for conflicting versions
npm dedupe  # Resolve duplicates
```

### Phase 6: Documentation and Knowledge Capture

Throughout the session, maintain comprehensive documentation.

#### 6.1 Update Documentation Continuously

As features are implemented, update docs:

```markdown
# API Documentation Update

## Authentication Endpoints

### POST /api/auth/login
Authenticate user and receive JWT tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200 OK):**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "expiresIn": 3600,
  "tokenType": "Bearer"
}
```

**Error Response (401):**
```json
{
  "error": "Invalid credentials",
  "message": "Email or password incorrect"
}
```
```

#### 6.2 Capture Lessons Learned

Document discoveries for future sessions:

```markdown
## Lessons Learned - Overnight Session $(date)

### What Worked Well
- TDD approach caught edge cases early
- Git hooks prevented broken commits
- Automated linting saved debugging time

### Challenges Encountered
- Token refresh logic required 3 iterations
- Race condition in concurrent login attempts
- Memory leak in token cache (fixed)

### Improvements for Next Session
- Add performance tests for high load
- Implement rate limiting earlier
- Create test fixtures for common scenarios
```

## Using Bundled Resources

### Utility Scripts

Leverage bundled automation scripts for common operations:

```bash
# Initialize overnight session
./scripts/init-overnight-session.sh \
  --task "Build payment integration" \
  --duration 8 \
  --coverage-target 90

# Validate hook configuration
./scripts/validate-hooks.py \
  --check-permissions \
  --verify-commands \
  --test-execution

# Generate session report
./scripts/generate-report.py \
  --log-file .overnight-dev-log.txt \
  --output-format markdown \
  --include-metrics
```

### Reference Documentation

Load detailed guides when needed:

- **TDD Best Practices:** `./references/tdd-methodology.md`
- **Common Test Patterns:** `./references/test-patterns.md`
- **Debugging Strategies:** `./references/debug-guide.md`
- **Git Hook Customization:** `./references/hook-configuration.md`

### Configuration Templates

Use templates for different technology stacks:

```bash
# Copy appropriate template
cp ./assets/configs/nodejs-jest.json .overnight-dev.json
cp ./assets/configs/python-pytest.json .overnight-dev.json
cp ./assets/configs/rust-cargo.json .overnight-dev.json
cp ./assets/configs/go-testing.json .overnight-dev.json

# Or use interactive configurator
./scripts/configure-overnight.sh --interactive
```

## Examples

### Example 1: Building Authentication System

**User Request:** "Set up overnight session to build JWT authentication with refresh tokens"

**Workflow:**

1. **Assess environment:**
   ```bash
   git status  # Confirm clean working tree
   npm test   # Verify existing tests pass
   ```

2. **Configure overnight development:**
   ```bash
   ./scripts/setup-overnight-hooks.sh
   echo '{"testCommand":"npm test","minCoverage":90}' > .overnight-dev.json
   ```

3. **Define test specifications:**
   ```javascript
   // Write comprehensive test suite first
   // 20+ test cases for auth functionality
   ```

4. **Begin TDD implementation:**
   - Write failing test for login
   - Implement minimal code to pass
   - Refactor and improve
   - Commit when all tests pass
   - Repeat for each feature

5. **Monitor progress:**
   ```bash
   tail -f .overnight-dev-log.txt
   # [22:15] Session started - 12/12 tests passing
   # [23:30] Login endpoint complete - 18/18 passing
   # [01:45] Token refresh working - 28/28 passing
   # [03:20] Rate limiting added - 35/35 passing
   # [05:00] Integration tests done - 47/47 passing
   # [06:30] Documentation updated - Coverage 94%
   ```

6. **Morning handoff:**
   - All 47 tests passing
   - 94% code coverage
   - 23 commits with clean history
   - Full API documentation
   - Production-ready authentication

### Example 2: Refactoring Legacy Module

**User Request:** "Refactor the payment processing module overnight with maintained test coverage"

**Workflow:**

1. **Establish baseline:**
   ```bash
   npm test -- --coverage payment/
   # Current: 72% coverage, 34 tests
   ```

2. **Create refactoring plan:**
   - Extract payment gateway interface
   - Implement repository pattern
   - Add dependency injection
   - Improve error handling

3. **Refactor with test protection:**
   ```bash
   # Each refactoring step:
   # 1. Run tests (must stay green)
   # 2. Make refactoring change
   # 3. Run tests (must stay green)
   # 4. Commit if passing
   ```

4. **Enhance test coverage:**
   - Add tests for edge cases
   - Test error scenarios
   - Add integration tests
   - Target: 90% coverage

5. **Results after 7 hours:**
   - Module successfully refactored
   - 52 tests (up from 34)
   - 91% coverage (up from 72%)
   - Performance improved by 40%
   - Clean SOLID architecture

### Example 3: Implementing Complex Feature

**User Request:** "Build real-time notifications system with WebSocket support overnight"

**Workflow:**

1. **Design test-first architecture:**
   ```javascript
   describe('Notification System', () => {
     describe('WebSocket Connection', () => {
       it('should establish connection with auth token');
       it('should reconnect on disconnect');
       it('should handle concurrent connections');
     });

     describe('Message Delivery', () => {
       it('should deliver to connected clients');
       it('should queue for offline users');
       it('should respect user preferences');
       it('should batch notifications');
     });

     describe('Scalability', () => {
       it('should handle 10,000 concurrent connections');
       it('should distribute load across workers');
     });
   });
   ```

2. **Implement incrementally:**
   - Phase 1: Basic WebSocket server (2 hours)
   - Phase 2: Authentication integration (1 hour)
   - Phase 3: Message routing (2 hours)
   - Phase 4: Offline queuing (1 hour)
   - Phase 5: Scaling features (2 hours)

3. **Continuous validation:**
   - Every commit requires all tests passing
   - Coverage must not decrease
   - Performance benchmarks must pass

4. **Morning success metrics:**
   - 67 tests all passing
   - 88% code coverage
   - Handles 15,000 concurrent connections
   - Average latency: 12ms
   - Zero memory leaks

## Best Practices

### Test-First Development

- Write test before implementation code
- One test at a time
- Minimal code to pass test
- Refactor only with green tests
- Never skip tests to "save time"

### Commit Discipline

- Atomic commits (one logical change)
- All commits must have passing tests
- Use conventional commit format
- No "WIP" or "temporary" commits
- Squash debugging commits before merge

### Error Handling

- Test error cases explicitly
- Handle all promise rejections
- Validate input thoroughly
- Provide meaningful error messages
- Log errors for debugging

### Code Quality

- Maintain consistent style
- Remove debug code before commit
- Document complex logic
- Keep functions small and focused
- Use meaningful variable names

## Troubleshooting

### Issue: Hooks Not Running

**Symptoms:** Commits succeed without running tests

**Solution:**
```bash
# Verify hooks are executable
ls -la .git/hooks/
# Should show: -rwxr-xr-x pre-commit

# Fix permissions if needed
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg

# Test hook manually
.git/hooks/pre-commit
```

### Issue: Tests Failing in Loop

**Symptoms:** Same test fails repeatedly despite fixes

**Solution:**
```bash
# Clear all caches
npm cache clean --force
jest --clearCache

# Reset test database
npm run db:reset

# Check for timing issues
jest --runInBand  # Run tests serially

# Increase timeout for slow operations
jest.setTimeout(10000);
```

### Issue: Coverage Decreasing

**Symptoms:** New code reduces overall coverage

**Solution:**
```bash
# Generate detailed coverage report
npm test -- --coverage --coverageReporters=lcov

# Find uncovered lines
grep -n "0x" coverage/lcov.info

# Add specific tests for gaps
npm test -- --coverage --collectCoverageFrom="src/auth/**"
```

### Issue: Commit Message Rejected

**Symptoms:** Valid code but commit fails on message

**Solution:**
```bash
# Use conventional commit format
git commit -m "type(scope): description"

# Valid types:
# feat: New feature
# fix: Bug fix
# docs: Documentation
# test: Test changes
# refactor: Code refactoring
# perf: Performance improvement
# chore: Maintenance
```

## Integration with Other Skills

### Complementary Skills

**devops-automation-pack:** Combine for CI/CD pipeline setup during overnight sessions

**web-to-github-issue:** Create issues for problems discovered during overnight debugging

**git-workflow-automation:** Enhanced Git operations during autonomous development

### Skill Composition Example

```markdown
## Overnight Session with Multiple Skills

1. **overnight-dev-autonomous-sessions** (Primary)
   - Manages TDD workflow
   - Enforces quality gates

2. **devops-automation-pack** (Supporting)
   - Sets up CI/CD pipeline
   - Configures deployment

3. **project-documentation** (Supporting)
   - Generates API docs
   - Updates README

Result: Complete feature with tests, CI/CD, and documentation
```

## Performance Optimization

### Session Efficiency Tips

- Run only affected tests during development
- Use test watchers for faster feedback
- Parallelize independent test suites
- Cache dependencies between runs
- Use incremental builds

### Resource Management

```bash
# Monitor resource usage during session
./scripts/monitor-resources.sh \
  --track-memory \
  --track-cpu \
  --alert-threshold 80

# Optimize test execution
npm test -- --maxWorkers=4  # Limit parallel processes
npm test -- --coverage=false  # Skip coverage during iteration
```

## Success Metrics

Track these KPIs for overnight sessions:

- **Test Success Rate:** Should reach 100% by morning
- **Code Coverage:** Maintain or improve (target: >80%)
- **Commits Per Hour:** 4-8 indicates good progress
- **Debug Iterations:** <3 per failure shows effective fixing
- **Lines of Code:** 500-1500 per session typical
- **Documentation Updates:** Should parallel code changes

## Summary

The overnight development autonomous sessions skill transforms Claude into a tireless developer that works through the night, enforcing quality through test-driven development and Git hooks. By establishing clear success criteria, implementing systematic debugging protocols, and maintaining comprehensive documentation, this approach delivers production-ready features while developers sleep. The morning brings not just completed code, but fully tested, documented, and quality-assured features ready for deployment.

Remember: **Don't stop until it's green.** The hooks enforce quality, the tests define success, and iteration brings victory. Every morning delivers the satisfaction of waking up to fully realized, production-ready features.