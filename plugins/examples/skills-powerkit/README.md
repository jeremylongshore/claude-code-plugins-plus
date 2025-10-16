# Skills Powerkit

**The ultimate demonstration of Claude Code Agent Skills** - 5 professional, auto-invoked capabilities that showcase the power of model-invoked skills.

[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)](.)
[![Skills](https://img.shields.io/badge/skills-5-blue)](.)
[![Type](https://img.shields.io/badge/type-example-orange)](.)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What Are Agent Skills?

**Agent Skills are model-invoked capabilities** that Claude automatically uses when relevant to your request. Unlike slash commands (which you explicitly type), skills activate automatically based on conversation context.

**Think of it like this:**
- **Slash Command**: You say "/format-code" → Claude formats code
- **Agent Skill**: You say "this code is messy" → Claude automatically uses code formatter skill

Skills make Claude **smarter and more context-aware** without requiring you to remember specific commands.

---

## 5 Included Skills

### 1. 🔍 Code Quality Analyzer
**Automatically analyzes code for quality issues**

**Activates when you mention:**
- Code quality, code review, analyze code
- Technical debt, refactoring
- Complexity, code smells, maintainability

**What it does:**
- Scans for high complexity hotspots
- Detects code smells (long methods, deep nesting, duplicates)
- Identifies anti-patterns
- Provides prioritized, actionable recommendations

**Example:** "Can you review the code quality in src/api/?"

---

### 2. ✅ Test Generator
**Automatically generates comprehensive test suites**

**Activates when you mention:**
- Generate tests, write tests
- Test coverage, unit tests
- Integration tests, test cases

**What it does:**
- Creates unit and integration tests
- Includes happy path + edge cases
- Generates mock configurations
- Supports Jest, pytest, JUnit, RSpec, and more

**Example:** "Generate tests for the UserService class"

---

### 3. 📝 Documentation Writer
**Automatically generates professional documentation**

**Activates when you mention:**
- Documentation, docs
- API documentation, README
- Explain code, add comments

**What it does:**
- Generates API documentation (JSDoc, docstrings)
- Creates README files with examples
- Adds inline code comments
- Writes user guides and tutorials

**Example:** "Create a README for this project"

---

### 4. 🔒 Security Scanner
**Automatically scans for security vulnerabilities**

**Activates when you mention:**
- Security, security scan, vulnerability
- Security review, OWASP
- Injection attacks, XSS, SQL injection

**What it does:**
- Scans for OWASP Top 10 vulnerabilities
- Identifies injection risks (SQL, XSS, command)
- Checks authentication/authorization issues
- Provides secure code examples and remediation

**Example:** "Check this code for security issues"

---

### 5. ⚡ Performance Optimizer
**Automatically identifies and fixes performance bottlenecks**

**Activates when you mention:**
- Performance, optimize, slow code
- Speed up, bottleneck
- Memory leak, improve performance

**What it does:**
- Identifies algorithm complexity issues (O(n²) → O(n))
- Detects memory leaks
- Finds N+1 query problems
- Provides optimized code with benchmarks

**Example:** "This function is slow, can you optimize it?"

---

## Installation

```bash
# Add marketplace (if not already added)
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install Skills Powerkit
/plugin install skills-powerkit@claude-code-plugins-plus
```

**That's it!** All 5 skills are now active and will automatically invoke when relevant.

---

## How to Use

**You don't need to do anything special** - just talk naturally!

### Example Conversations

**Conversation 1: Code Review**
```
You: "I need to review the authentication code for security issues and code quality"

Claude automatically:
1. Recognizes "security issues" → Invokes Security Scanner
2. Recognizes "code quality" → Invokes Code Quality Analyzer
3. Scans authentication code with both skills
4. Reports security vulnerabilities + quality issues
5. Provides fixes and recommendations
```

**Conversation 2: New Feature**
```
You: "I added a payment processing function, need tests and docs"

Claude automatically:
1. Recognizes "need tests" → Invokes Test Generator
2. Recognizes "docs" → Invokes Documentation Writer
3. Generates comprehensive test suite
4. Creates API documentation
5. Delivers both without you asking twice
```

**Conversation 3: Performance Issue**
```
You: "The search endpoint is slow, optimize it"

Claude automatically:
1. Recognizes "slow, optimize" → Invokes Performance Optimizer
2. Analyzes search endpoint code
3. Identifies bottlenecks (probably N+1 queries)
4. Provides optimized version with benchmarks
```

---

## Skills vs Commands

| Feature | Skills (This Plugin) | Slash Commands |
|---------|---------------------|----------------|
| **Invocation** | Automatic (Claude decides) | Manual (you type `/command`) |
| **Trigger** | Keywords in conversation | Explicit `/command` |
| **Intelligence** | Context-aware | Single-purpose |
| **User Experience** | Natural conversation | Command-driven |
| **Example** | "check security" → auto-scans | `/security-scan` → scans |

**Skills feel more natural** - like talking to an expert who knows when to use their capabilities.

---

## Demo Command

Want to see all skills in action? Try the demo command:

```bash
/demo-skills
```

This shows examples of how each skill auto-invokes and what triggers them.

---

## Included Slash Commands

### `/demo-skills`
Comprehensive guide to all 5 skills with trigger examples and use cases.

---

## Technical Details

### Skill Restrictions

All skills use **read-only or minimal write access** for safety:

| Skill | Allowed Tools |
|-------|--------------|
| Code Quality Analyzer | Read, Grep (read-only) |
| Test Generator | Read, Write, Grep |
| Documentation Writer | Read, Write, Grep |
| Security Scanner | Read, Grep (read-only) |
| Performance Optimizer | Read, Grep (read-only) |

**Safe for production use** - no destructive operations!

### Skill Structure

Each skill follows Claude Code's SKILL.md format:

```
skills/
├── code-analyzer/
│   └── SKILL.md
├── test-generator/
│   └── SKILL.md
├── doc-writer/
│   └── SKILL.md
├── security-scanner/
│   └── SKILL.md
└── performance-optimizer/
    └── SKILL.md
```

---

## Use Cases

### For Developers
- Code reviews with automatic quality + security analysis
- Test generation for new features
- Documentation creation without context switching
- Performance optimization with benchmarks

### For Teams
- Consistent code quality standards
- Security-first development
- Comprehensive test coverage
- Professional documentation

### For Learning
- See how professional skills are structured
- Understand model-invoked vs user-invoked
- Use as templates for your own skills
- Learn skill authoring best practices

---

## Why This Plugin?

**Skills Powerkit demonstrates the future of AI-assisted development:**

1. **Context-Aware** - Claude knows when to use each capability
2. **Natural Interaction** - No memorizing commands
3. **Multiple Skills** - Different skills work together seamlessly
4. **Professional Quality** - Production-ready skill examples
5. **Educational** - Learn by example from well-crafted skills

**This is what makes Claude Code + Skills powerful** - AI that understands context and applies the right tools automatically.

---

## Requirements

- Claude Code CLI
- Claude Code version with Skills support (October 2025+)
- Pro, Team, or Enterprise plan (Skills require code execution)

---

## Security Note

⚠️ **Skills can execute code** through Claude's Code Execution Tool. This plugin's skills are designed with safety in mind:

- Read-only tools where possible
- No destructive operations
- No external API calls
- Safe for production codebases

**Always review skills from unknown sources before installation.**

---

## Examples in the Wild

**Example 1: Full Feature Development**
```
You: "Build user authentication with JWT tokens"

Skills automatically activate:
1. Security Scanner → Validates auth implementation security
2. Test Generator → Creates auth tests
3. Documentation Writer → Generates API docs
4. Code Quality Analyzer → Reviews code structure
```

**Example 2: Legacy Code Maintenance**
```
You: "Refactor this old module - it's slow and messy"

Skills automatically activate:
1. Performance Optimizer → Identifies bottlenecks
2. Code Quality Analyzer → Finds quality issues
3. Test Generator → Adds missing tests (for safety)
4. Documentation Writer → Explains refactored code
```

**Example 3: Security Audit**
```
You: "Full security audit of the API layer"

Skills automatically activate:
1. Security Scanner → OWASP Top 10 scan
2. Code Quality Analyzer → Finds security-impacting code smells
3. Documentation Writer → Documents security requirements
```

---

## Contributing

Want to improve these skills? Found a bug?

**Report issues:** https://github.com/jeremylongshore/claude-code-plugins/issues

**Submit improvements:** Fork, enhance, and create PR

---

## License

MIT License - See [LICENSE](LICENSE) file

---

## Learn More

- **Agent Skills Documentation:** https://docs.claude.com/en/docs/claude-code/skills
- **Plugin Guide:** https://docs.claude.com/en/docs/claude-code/plugins
- **Marketplace:** https://claudecodeplugins.io

---

## Changelog

### v1.0.0 (2025-10-16)
- Initial release
- 5 professional Agent Skills
- Demo command
- Comprehensive documentation

---

**Ready to experience the future of AI-assisted development?**

```bash
/plugin install skills-powerkit@claude-code-plugins-plus
```

Then just start coding - the skills will help when you need them! 🚀
