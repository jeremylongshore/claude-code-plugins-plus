# PI Pathfinder

**Finds the path through 229 plugins** 🎯

You don't pick plugins - PI does. Smart pathfinder that analyzes your request, automatically selects the best plugin, extracts its skills, and applies them.

**Ultra-think mode: OFF | Easy mode: ON**

[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)](.)
[![Agent Skills](https://img.shields.io/badge/agent--skills-1-blue)](.)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Problem You Had

229 plugins installed. Which one do you use? Who remembers?

**BEFORE:**
```
You: "Scan my code for security issues"
You: *thinks* "Which plugin was that?"
You: *searches marketplace*
You: *reads docs*
You: *tries command*
Result: Wrong plugin
```

**NOW:**
```
You: "Scan my code for security issues"
PI Pathfinder: *picks best plugin automatically*
PI Pathfinder: *extracts its skills*
PI Pathfinder: *runs it*
Done. Zero thinking from you.
```

---

## How It Works

**You:** Describe what you want in plain English

**PI Pathfinder:**
1. Understands your task
2. Searches your installed plugins (all 228 if you want)
3. Picks the best one(s) automatically
4. Extracts how they work
5. Applies their skills to your problem
6. Done

**You never:**
- ❌ Pick plugins
- ❌ Remember names
- ❌ Read docs
- ❌ Run commands

---

## Real Examples

### "Check my code for vulnerabilities"

```
PI Pathfinder automatically:
✓ Searches your plugins for: security, scan, vulnerability
✓ Finds: owasp-scanner + security-audit + code-quality
✓ Extracts all 3 approaches
✓ Combines: OWASP checks + security audit + quality scan
✓ Runs on your code
✓ Reports: "Found 3 SQL injection risks, 2 XSS issues"

You did: 5 words
PI Pathfinder did: Everything else
```

### "Deploy my app"

```
PI Pathfinder automatically:
✓ Searches: deploy, automation, docker
✓ Finds: deployment-pipeline + docker-composer
✓ Extracts: Build → Test → Deploy workflow
✓ Runs your deployment
✓ Reports: "Deployed. Health checks passing."

You did: 3 words
PI Pathfinder did: Entire deployment
```

### "Make API docs"

```
PI Pathfinder automatically:
✓ Searches: documentation, api, swagger
✓ Finds: api-documenter + swagger-generator
✓ Extracts how they work
✓ Scans your API code
✓ Generates: OpenAPI spec + Swagger UI + Markdown
✓ Done: "Created docs in /docs/"

You did: 3 words
PI Pathfinder did: Complete documentation system
```

---

## Why This Is Better

### Old Way
```
1. Figure out which plugin
2. Remember its name
3. Look up command
4. Run it
5. Hope it's right
```

### New Way
```
1. Say what you want
[PI Pathfinder does 2-5]
Done.
```

---

## Installation

```bash
# Add marketplace
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install PI Pathfinder  
/plugin install pi-pathfinder@claude-code-plugins-plus

# Install plugins you want (as many as you want)
/plugin install devops-automation-pack@claude-code-plugins-plus
/plugin install security-toolkit@claude-code-plugins-plus
# Install 10, 50, or all 228 - doesn't matter

# Just talk normally
"Deploy my app"
"Check for bugs"  
"Generate docs"
```

PI Pathfinder picks the right plugins automatically.

---

## Usage - Zero Thinking

Just say what you want:

```bash
# Security
"Scan for vulnerabilities"
"Check for SQL injection"
"Audit dependencies"

# Documentation
"Generate API docs"
"Create README"
"Document this code"

# Testing
"Write tests"
"Run coverage"
"Check test failures"

# Deployment
"Deploy to staging"
"Build containers"
"Update production"

# Code Quality
"Check code quality"
"Find code smells"
"Fix issues"
```

PI Pathfinder figures out which plugins to use, extracts their skills, applies them.

**You never pick. It picks for you.**

---

## The Smart Part

### Learns Plugins On-The-Fly

Reads plugin source code and figures out how they work:
- commands/*.md (what they do)
- agents/*.md (how they think)
- skills/*/SKILL.md (capabilities)
- scripts/*.sh (implementation)

### Combines Multiple Plugins

```
Your task: "Check my code"

Finds: formatter + linter + security scanner
Combines: Format check + Lint + Security scan
Result: Comprehensive analysis
```

### Adapts to Your Context

```
Found: javascript-linter
Your code: Python
Adapts: Same linting logic with Python tools
Works: On your Python code
```

---

## What It Does (Behind the Scenes)

**1. Task Analysis:**
"Scan for security issues" → Security analysis → Vulnerability scanning

**2. Plugin Discovery:**
Searches your plugins → Finds matches → Ranks by relevance

**3. Skill Extraction:**
Reads how plugins work → Extracts approaches → Combines strategies

**4. Skill Application:**
Applies learned skills → Runs analysis → Reports results

**All automatic.**

---

## Limitations

**Can do:**
✅ 221 AI instruction plugins (commands, agents, skills)
✅ Analyze MCP plugin patterns
✅ Combine multiple plugins
✅ Adapt to your context
✅ All installed plugins

**Cannot do:**
❌ Execute compiled MCP code directly
❌ Use plugins needing API keys (unless you have them)
❌ Plugins you haven't installed
❌ Guarantee 100% accuracy (AI reasoning)

---

## Easy Mode ON 🎯

**The whole point:**
You shouldn't think about which plugin to use.

You installed plugins because they're useful.
PI Pathfinder makes sure you USE them without thinking.

Just describe what you want.
It handles the rest.

---

## One Solution to Manage All Your Plugins

Install once. Use forever.
Never pick plugins again.

**Ultra-think: OFF**
**Easy: ON** 🎯

---

## License

MIT - See LICENSE file
