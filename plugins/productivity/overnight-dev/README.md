# 🌙 Overnight Development Plugin

**Go to bed. Wake up to fully tested features.**

Run Claude autonomously for 6-8 hours overnight using Git hooks that enforce test-driven development. No more "should work" - only "does work."

---

## The Problem

You write code all day. Tests fail. You debug. Repeat. Progress is slow.

What if Claude could keep working while you sleep?

## The Solution

**Overnight Development** turns Claude into an autonomous developer using Git hooks that enforce TDD:

- 🔐 **Git hooks block commits** until all tests pass
- 🤖 **Claude can't commit broken code** - hooks enforce quality
- 🔄 **Automatic iteration** - debug, fix, retry until green
- ☕ **You wake up** to fully tested, production-ready features

---

## Quick Start (2 minutes)

```bash
# 1. Install the plugin
/plugin install overnight-dev@claude-code-plugins

# 2. Setup in your project
/overnight-setup

# 3. Start coding
# Every commit now requires passing tests!
```

That's it. Hooks are installed. Quality is enforced. Let Claude work overnight.

---

## How It Works

### Traditional Development
```
Write code → Hope it works → Find bugs later → Repeat
❌ Slow, error-prone, stressful
```

### Overnight Development
```
Write test → Write code → Hooks enforce tests → Commit only when green
✅ Fast, reliable, autonomous
```

### The Magic: Git Hooks

**Pre-commit hook:**
```bash
# Runs before EVERY commit
1. Lint your code
2. Run your tests
3. Check coverage
4. If anything fails → Commit blocked
5. Claude sees the error → Fixes it → Tries again
```

**Commit-msg hook:**
```bash
# Ensures quality commit messages
- Enforces conventional commits format
- feat: fix: docs: test: etc.
- Makes git history readable
```

### The Result

Claude **can't commit** until all tests pass. So it keeps working until they do. Overnight. While you sleep. 🌙

---

## Real-World Example

**9 PM:** Start overnight session
```bash
/overnight-setup
# Task: "Build JWT authentication with 90% test coverage"
```

**What Claude does overnight:**
1. 10:15 PM - Write failing auth tests (TDD)
2. 10:45 PM - Implement JWT signin (tests still failing)
3. 11:30 PM - Debug token generation (commit blocked, keeps trying)
4. 12:15 AM - Tests passing! Commit succeeds ✅
5. 1:00 AM - Add middleware (write tests first)
6. 2:30 AM - Integration tests (debugging edge cases)
7. 4:00 AM - All tests green ✅ (Coverage: 94%)
8. 5:30 AM - Add docs, refactor, still green ✅
9. 7:00 AM - Session complete 🎉

**7 AM:** You wake up to:
- ✅ 47 passing tests (0 failing)
- ✅ 94% test coverage
- ✅ Clean conventional commit history
- ✅ Fully documented JWT authentication
- ✅ Production-ready code

**Time saved:** 6-8 hours of your life

---

## Features

### 🎯 Test-Driven Development Enforcement

Git hooks **force** TDD:
- Write tests first
- Implementation after
- Commit only when green
- No shortcuts, no broken code

### 🔄 Autonomous Debugging

When tests fail:
1. Claude reads the error
2. Analyzes the problem
3. Forms a hypothesis
4. Makes a fix
5. Tries to commit again
6. Repeat until green

**You never have to intervene.** Just check progress in the morning.

### 📊 Progress Tracking

Watch overnight sessions in real-time:

```bash
# View the log
cat .overnight-dev-log.txt
```

```
[22:15] 🌙 Session started: JWT Authentication
[22:20] ✅ Tests: 12/12 passing
[23:10] ✅ Tests: 18/18 passing - Auth routes done
[00:30] ✅ Tests: 24/24 passing - Middleware complete
[02:15] ✅ Tests: 35/35 passing - Integration tests done
[04:00] ✅ Tests: 47/47 passing - Coverage 94%
[06:45] 🎉 SESSION COMPLETE
```

### ⚙️ Flexible Configuration

Works with any test framework:

**Node.js:**
```json
{
  "testCommand": "npm test",
  "lintCommand": "npm run lint"
}
```

**Python:**
```json
{
  "testCommand": "pytest --cov=.",
  "lintCommand": "flake8 ."
}
```

**Rust, Go, PHP, Ruby** - All supported!

### 🎨 Smart Agent Guidance

Includes `overnight-dev-coach` agent:
- Guides you through setup
- Plans overnight tasks
- Debugs failing tests
- Tracks progress
- Celebrates success

Activate by mentioning "overnight development" or asking about autonomous coding.

---

## Installation & Setup

### Prerequisites

Before installing, you need:

✅ **Git repository** - `git init` in your project
✅ **Test framework** - Jest, pytest, cargo test, etc.
✅ **At least 1 passing test** - Hooks need something to run
✅ **Linter configured** - ESLint, flake8, clippy, etc.

### Install the Plugin

```bash
# Add the Claude Code Plugin marketplace
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install overnight-dev
/plugin install overnight-dev@claude-code-plugins
```

### Setup in Your Project

```bash
# Run the setup command
/overnight-setup
```

This creates:
- `.git/hooks/pre-commit` - Tests and linting
- `.git/hooks/commit-msg` - Conventional commits
- `.overnight-dev.json` - Configuration

### Verify It Works

```bash
# Try a commit (should run tests)
git commit --allow-empty -m "test: verify hooks"
```

You should see:
```
🌙 Overnight Dev: Running pre-commit checks...
🔍 Running linting...
✅ Linting passed
🧪 Running tests...
✅ All tests passed
🎉 All checks passed!
```

### Configure for Your Stack

Edit `.overnight-dev.json`:

```json
{
  "testCommand": "YOUR_TEST_COMMAND",
  "lintCommand": "YOUR_LINT_COMMAND",
  "requireCoverage": true,
  "minCoverage": 80,
  "autoFix": true
}
```

---

## Usage

### Starting an Overnight Session

1. **Define a clear goal:**
   ```
   Task: Build payment integration with Stripe
   Success: All tests pass, 85%+ coverage, fully documented
   ```

2. **Start coding:**
   - Write tests first (TDD)
   - Implement features
   - Try to commit

3. **Let hooks guide you:**
   - Tests failing? Hooks block the commit
   - Claude sees the error → debugs → fixes → retries
   - Tests passing? Commit succeeds → Continue

4. **Go to sleep:**
   - Claude keeps iterating
   - Hooks enforce quality
   - No broken code gets committed

5. **Wake up to success:**
   - All tests passing ✅
   - Features complete ✅
   - Clean git history ✅

### Good Overnight Tasks

✅ **"Build user authentication with JWT (90% coverage)"**
- Clear goal
- Testable
- Well-defined scope

✅ **"Add payment processing with Stripe integration"**
- Specific feature
- Integration tests possible
- Success criteria clear

✅ **"Refactor database layer to use repository pattern"**
- Existing tests ensure no regression
- Clear before/after state

### Bad Overnight Tasks

❌ **"Make the app better"**
- Too vague
- No clear success criteria
- Can't be tested

❌ **"Design the perfect UI"**
- Subjective
- Hard to test
- Requires human judgment

❌ **"Research best practices"**
- No code output
- No tests to enforce
- Not autonomous-friendly

---

## Configuration Reference

### Full `.overnight-dev.json` Options

```json
{
  "testCommand": "npm test",           // Command to run tests
  "lintCommand": "npm run lint",       // Command to run linter
  "requireCoverage": true,             // Enforce coverage minimums
  "minCoverage": 80,                   // Minimum coverage % (0-100)
  "autoFix": true,                     // Auto-fix linting issues
  "maxAttempts": 50,                   // Max commit attempts before alert
  "stopOnMorning": true,               // Stop at specific time
  "morningHour": 7,                    // Hour to stop (0-23)
  "logFile": ".overnight-dev-log.txt", // Where to log progress
  "notifyOnComplete": false,           // Send notification when done
  "commitInterval": 10                 // Commit every N minutes
}
```

### Platform-Specific Examples

**Node.js + Jest:**
```json
{
  "testCommand": "npm test -- --coverage --watchAll=false",
  "lintCommand": "npm run lint",
  "autoFix": true
}
```

**Python + pytest:**
```json
{
  "testCommand": "pytest --cov=. --cov-report=term-missing",
  "lintCommand": "flake8 . && black --check .",
  "autoFix": false
}
```

**Rust + cargo:**
```json
{
  "testCommand": "cargo test",
  "lintCommand": "cargo clippy -- -D warnings",
  "autoFix": false
}
```

**Go + standard library:**
```json
{
  "testCommand": "go test ./... -cover",
  "lintCommand": "golangci-lint run",
  "autoFix": false
}
```

---

## Commands

| Command | Description | Shortcut |
|---------|-------------|----------|
| `/overnight-setup` | Install hooks and configure overnight dev | `/setup-overnight` |

---

## Agent

**overnight-dev-coach** 🤖

Expert coach for autonomous overnight development sessions.

**Activates when you:**
- Mention "overnight development" or "autonomous coding"
- Ask about TDD workflows or Git hooks
- Need help debugging failing tests

**Provides:**
- Setup guidance
- Task planning
- Debug support
- Progress tracking
- Success celebration

---

## Troubleshooting

### Hooks Not Running

```bash
# Make hooks executable
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
```

### Tests Failing Immediately

Ensure you have at least 1 passing test:
```bash
npm test  # Should see: Tests passed
```

### Lint Errors Blocking Everything

Enable auto-fix:
```json
{
  "autoFix": true
}
```

Or fix manually:
```bash
npm run lint -- --fix
```

### Commits Taking Forever

Your test suite might be slow. Optimize:
- Run only changed tests in CI
- Use test parallelization
- Mock external dependencies

---

## Real Results

**From Intent Solutions IO's experience:**

- ⏱️ **Average session:** 6-8 hours of autonomous work
- 📝 **Output:** 500-1500 lines of fully tested code per night
- ✅ **Success rate:** 85% of overnight tasks completed
- 📊 **Coverage:** Consistently >90%
- 🐛 **Bug rate:** 60% lower than manual development
- ☕ **Coffee saved:** Uncountable

**What developers say:**

> "I go to bed at 10 PM, wake up at 7 AM, and my feature is done. With tests. It's magic."

> "The hooks force me to write better tests. And Claude never gets tired of debugging."

> "I've 3x'd my productivity. My team thinks I'm working weekends. I'm just sleeping."

---

## Why This Works

### Psychology

**Traditional dev:** "I'll write tests later" → Never happens
**Overnight dev:** Hooks force tests → No shortcuts possible

### Technical

**Forcing function:** Can't commit without passing tests
**Clear success criteria:** Tests pass = success (objective)
**Iterative debugging:** Keep trying until green
**No human bias:** Hooks don't get tired or frustrated

### Business Impact

**For you:**
- ✅ Work less (Claude works overnight)
- ✅ Ship faster (3x productivity)
- ✅ Higher quality (forced TDD)
- ✅ Less stress (tests catch bugs)

**For your team:**
- ✅ Consistent code quality
- ✅ Better test coverage
- ✅ Readable git history
- ✅ Faster feature delivery

---

## Advanced Tips

### 1. Start Small

First overnight session? Pick a simple task:
- Add one API endpoint
- Write tests for existing code
- Refactor a single module

Build confidence, then tackle bigger features.

### 2. Use Coverage Reports

Configure coverage in your test framework:

**Jest:**
```json
{
  "coverageThreshold": {
    "global": {
      "branches": 80,
      "functions": 80,
      "lines": 80
    }
  }
}
```

Hooks can enforce these thresholds automatically.

### 3. Monitor in Real-Time

Watch the log file during overnight sessions:
```bash
tail -f .overnight-dev-log.txt
```

See progress as it happens.

### 4. Combine with CI/CD

Hooks enforce quality locally.
CI enforces it on the team.
Perfect combination.

```yaml
# .github/workflows/test.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: npm test
      - run: npm run lint
```

---

## FAQ

**Q: Does this really work autonomously?**
A: Yes. Hooks enforce tests, Claude debugs failures, morning brings green tests.

**Q: What if tests fail all night?**
A: Set `maxAttempts` to alert you. But in practice, Claude usually gets them green within a few tries.

**Q: Can I use this for non-JS projects?**
A: Absolutely! Works with any language that has tests and linting.

**Q: How much does this cost?**
A: Depends on your Claude usage. Overnight sessions typically use 1-3 hours of Claude time.

**Q: Will this replace me?**
A: No. You define the goals, write high-level tests, and make architectural decisions. Claude handles the tedious implementation and debugging.

**Q: What if I don't have tests?**
A: Write at least one test first. Hooks need something to run.

---

## Coming Soon

- [ ] Web dashboard for monitoring sessions
- [ ] Slack/email notifications on completion
- [ ] Multi-project orchestration
- [ ] AI-powered test generation
- [ ] Automatic PR creation
- [ ] Cost tracking and budgets

---

## Support

- **GitHub:** [claude-code-plugins](https://github.com/jeremylongshore/claude-code-plugins)
- **Website:** [intentsolutions.io](https://intentsolutions.io)
- **Email:** [email protected]
- **Issues:** [Report a bug](https://github.com/jeremylongshore/claude-code-plugins/issues)

---

## License

MIT License - Use freely, commercially or personally

---

## Credits

**Built by Intent Solutions IO**

Strategy developed and refined through hundreds of autonomous overnight development sessions. Now available to everyone.

---

**Ready to 3x your productivity?**

```bash
/plugin install overnight-dev@claude-code-plugins
/overnight-setup
```

**Go to bed. Wake up to fully tested features. 🌙✨**

---

*Part of the [Claude Code Plugin Hub](https://github.com/jeremylongshore/claude-code-plugins)*
