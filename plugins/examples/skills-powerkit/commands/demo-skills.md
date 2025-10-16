---
name: demo-skills
description: Demonstrates the 5 Agent Skills in this plugin with examples of how each skill auto-invokes
model: sonnet
---

# Skills Powerkit Demo

This command demonstrates the 5 Agent Skills included in this plugin and how they automatically activate based on your requests.

## Included Skills

### 1. Code Quality Analyzer
**Auto-invokes when you mention:**
- "code quality", "code review", "analyze code"
- "technical debt", "refactoring"
- "complexity", "code smell"

**Example request:** "Can you review the code quality in src/api/?"

**What it does:**
- Scans for complexity hotspots
- Detects code smells (long methods, deep nesting)
- Identifies anti-patterns
- Provides prioritized recommendations

---

### 2. Test Generator
**Auto-invokes when you mention:**
- "generate tests", "write tests"
- "test coverage", "unit test"
- "integration test"

**Example request:** "Generate tests for the UserService class"

**What it does:**
- Creates comprehensive test suites
- Includes happy path + edge cases
- Generates mock configurations
- Supports Jest, pytest, JUnit, RSpec, etc.

---

### 3. Documentation Writer
**Auto-invokes when you mention:**
- "documentation", "docs", "write documentation"
- "API documentation", "README"
- "explain this code", "add comments"

**Example request:** "Create a README for this project"

**What it does:**
- Generates API documentation
- Creates README files
- Adds inline comments
- Writes user guides

---

### 4. Security Scanner
**Auto-invokes when you mention:**
- "security", "security scan", "vulnerability"
- "security review", "OWASP"
- "injection attack", "XSS", "SQL injection"

**Example request:** "Check this code for security issues"

**What it does:**
- Scans for OWASP Top 10 vulnerabilities
- Identifies injection risks
- Checks authentication/authorization
- Provides secure code examples

---

### 5. Performance Optimizer
**Auto-invokes when you mention:**
- "performance", "optimize", "slow"
- "speed up", "bottleneck"
- "memory leak", "improve performance"

**Example request:** "This function is slow, can you optimize it?"

**What it does:**
- Identifies algorithm complexity issues
- Detects memory leaks
- Finds database query problems
- Provides optimized code with benchmarks

---

## How Skills Work

**Skills are MODEL-INVOKED** - Claude automatically decides when to use them based on your request.

**Example conversation:**

**You:** "I need to review the authentication code for security issues"

**Claude automatically:**
1. Recognizes "security issues" keyword
2. Invokes Security Scanner skill
3. Scans authentication code
4. Reports vulnerabilities
5. Provides secure fixes

You didn't need to explicitly trigger anything - Claude understood context and used the right skill!

---

## Skills vs Commands

| Feature | Skills | Commands |
|---------|--------|----------|
| **Invocation** | Auto (Claude decides) | Manual (you type `/command`) |
| **Trigger** | Keywords in conversation | Explicit command |
| **Use Case** | Background capabilities | Specific workflows |

---

## Try It Out!

Test each skill by saying things like:

1. **"Analyze the code quality in this file"** → Code Analyzer activates
2. **"Generate unit tests for this class"** → Test Generator activates
3. **"Add documentation to these functions"** → Documentation Writer activates
4. **"Security review of the API endpoints"** → Security Scanner activates
5. **"This query is slow, optimize it"** → Performance Optimizer activates

Claude will automatically use the right skill based on what you're asking for!

---

## Installing Skills Powerkit

```bash
/plugin install skills-powerkit@claude-code-plugins-plus
```

Once installed, all 5 skills are immediately available and will auto-invoke when relevant.

---

**Need help?** Just ask "What skills do I have available?" and Claude will list all your active skills!
