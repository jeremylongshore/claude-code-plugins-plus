# How Agent Skills Activate - User Guide

**Last Updated:** November 8, 2025
**Applies to:** All plugins with Agent Skills (175 plugins)

## Quick Start: Making Skills Work

**The #1 Complaint:** "I installed plugins but they never activate!"

**The Solution:** Skills activate based on **trigger phrases** in your requests. You need to use the right words!

## How Skill Activation Works

### 1. Skills Are Always Listening

When you install a plugin with skills, Claude automatically:
- ✅ Loads the skill descriptions
- ✅ Monitors your conversation for trigger phrases
- ✅ Activates skills when triggers are detected
- ⚠️ **But you won't see a notification** - skills work silently in the background

### 2. Trigger Phrases Activate Skills

Each skill includes trigger phrases in its description. For example:

**Performance CPU Monitor Skill:**
```
Use this skill when the user asks to "monitor CPU usage",
"optimize CPU performance", "analyze CPU load", or "find CPU bottlenecks".
```

**To activate this skill, say:**
- ✅ "Monitor CPU usage in my app"
- ✅ "Analyze CPU load and find bottlenecks"
- ✅ "Optimize CPU performance"

**What WON'T activate it:**
- ❌ "My app is slow" (too vague)
- ❌ "Check performance" (doesn't mention CPU)
- ❌ "Help me" (no trigger keywords)

### 3. Be Specific with Your Requests

Skills activate best when you:
- **Use exact trigger phrases** from the skill description
- **Mention the specific task** (CPU, database, security, etc.)
- **Use action verbs** (analyze, monitor, detect, optimize, etc.)

## Finding Trigger Phrases

### Method 1: Read the Plugin Description

When installing a plugin, read its description carefully:

```bash
/plugin install cpu-usage-monitor@claude-code-plugins-plus
```

The description will show trigger phrases like:
- "monitor CPU usage"
- "optimize CPU performance"
- "find CPU bottlenecks"

### Method 2: Check the Plugin README

Visit the plugin directory and read the README.md:

```bash
plugins/performance/cpu-usage-monitor/README.md
```

Look for sections like:
- **Trigger Keywords**
- **When to Use**
- **Activation Examples**

### Method 3: View the SKILL.md File

For detailed trigger info, check the SKILL.md file:

```bash
plugins/performance/cpu-usage-monitor/skills/cpu-usage-monitor/SKILL.md
```

The description field contains all trigger phrases.

## Common Activation Patterns

### Security Skills

**Trigger words:** security, vulnerability, scan, audit, threat

**Examples:**
- "Scan for security vulnerabilities"
- "Audit authentication mechanisms"
- "Check for security threats"

### Testing Skills

**Trigger words:** test, testing, coverage, unit test, integration test

**Examples:**
- "Generate unit tests for this function"
- "Run integration tests"
- "Check test coverage"

### Code Analysis Skills

**Trigger words:** analyze, detect, find, identify, review

**Examples:**
- "Analyze code for bottlenecks"
- "Detect code smells"
- "Review this function for issues"

### Database Skills

**Trigger words:** database, query, migration, schema, SQL

**Examples:**
- "Optimize database queries"
- "Create a migration"
- "Design database schema"

### Performance Skills

**Trigger words:** performance, optimize, slow, bottleneck, CPU, memory

**Examples:**
- "Optimize performance of this code"
- "Find memory leaks"
- "Analyze CPU usage"

## Why You Don't See Activation Notifications

**By Design:** Skills work silently to avoid interrupting your workflow.

**How to Know a Skill Activated:**

1. **Check Claude's response** - Does it:
   - Use terminology from the skill?
   - Follow the skill's workflow?
   - Provide the specific type of analysis you requested?

2. **Look for skill-specific output** - Many skills:
   - Generate reports in a specific format
   - Use specific tools (Read, Grep, Bash)
   - Provide structured recommendations

3. **Observe Claude's behavior** - Skills often:
   - Ask follow-up questions specific to the skill
   - Use specialized knowledge
   - Apply domain-specific best practices

## Troubleshooting: "My Skill Won't Activate"

### Problem 1: Using Wrong Trigger Words

**Symptom:** You installed a testing plugin but Claude doesn't generate tests

**Solution:** Use exact trigger phrases:
- ❌ "Make some tests" (vague)
- ✅ "Generate unit tests for this function" (specific trigger)

### Problem 2: Plugin Not Installed

**Symptom:** Nothing happens when using trigger phrases

**Solution:** Verify installation:
```bash
/plugin list
```

If not shown, install it:
```bash
/plugin install <plugin-name>@claude-code-plugins-plus
```

### Problem 3: Conflicting Plugins

**Symptom:** Wrong skill activates

**Solution:** Be more specific in your request:
- ❌ "Test this" → Could trigger any testing skill
- ✅ "Run integration tests for API endpoints" → Specific skill

### Problem 4: Plugin Not in Current Context

**Symptom:** Skill should activate but doesn't

**Solution:** Some skills need file context:
- Open relevant files first
- Provide code snippets
- Mention file paths explicitly

## Maximizing Skill Effectiveness

### 1. Combine Multiple Triggers

**Good:**
"Analyze CPU usage and optimize performance"

**Better:**
"Monitor CPU usage patterns, identify bottlenecks, and recommend optimizations"

### 2. Provide Context

**Good:**
"Generate tests"

**Better:**
"Generate unit tests for the authentication module in src/auth/login.ts"

### 3. Use Progressive Refinement

**First Request:**
"Analyze this code for performance issues"

**If generic response:**
"Specifically check CPU usage and memory allocation"

### 4. Reference the Plugin Explicitly

**Option:**
"Use the cpu-usage-monitor skill to analyze this function"

This forces activation of that specific skill.

## Skill Permission System (2025 Schema)

All skills now specify which tools they can use via `allowed-tools`:

### Read-Only Skills
```yaml
allowed-tools: Read, Grep, Glob, Bash
```
**Can:** Analyze code, read files, search content
**Cannot:** Modify any files

### Code Editing Skills
```yaml
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
```
**Can:** Analyze AND modify code
**Cannot:** Access web resources

### Research Skills
```yaml
allowed-tools: Read, WebFetch, WebSearch, Grep
```
**Can:** Search the web, fetch documentation
**Cannot:** Modify code

**Why this matters:** Understanding tool permissions helps you know what a skill can/cannot do.

## 175 Skills Available

Browse the marketplace to find skills for:
- 🔒 Security (authentication, vulnerability scanning, encryption)
- 📊 Performance (CPU monitoring, memory optimization, load testing)
- 🧪 Testing (unit tests, integration tests, E2E, visual regression)
- 🗄️ Database (migrations, queries, schema design, optimization)
- 🚀 DevOps (CI/CD, deployment, Docker, Kubernetes)
- 📚 Documentation (README generation, API docs, changelogs)
- 🤖 AI/ML (model training, data preprocessing, pipelines)
- And many more!

**Browse all plugins:**
```bash
/plugin marketplace list
```

## Getting Help

### If Skills Still Won't Activate:

1. **Check the skill description** - Read the exact trigger phrases
2. **Verify installation** - Run `/plugin list`
3. **Use explicit triggers** - Copy trigger phrases from docs
4. **Ask Claude** - "What skills are available for database optimization?"
5. **Report issues** - [GitHub Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)

### Join the Community

- **Discord:** [#claude-code channel](https://discord.com/invite/6PPFFzqPDZ)
- **GitHub Discussions:** Share tips and tricks
- **Contribute:** Help improve skill descriptions

## Best Practices Summary

✅ **DO:**
- Use specific trigger phrases from skill descriptions
- Mention the task domain (security, testing, database, etc.)
- Provide file context when relevant
- Combine multiple related triggers

❌ **DON'T:**
- Use vague requests ("help me", "check this")
- Assume skills activate automatically without triggers
- Mix unrelated domains in one request
- Expect activation notifications (they're silent)

## Examples: Before & After

### Example 1: Security Scanning

**Before (won't activate):**
"Is my code safe?"

**After (activates security scan skill):**
"Scan this authentication code for security vulnerabilities and check for SQL injection risks"

### Example 2: Test Generation

**Before (won't activate):**
"I need tests"

**After (activates unit test generator):**
"Generate unit tests for the UserService class with coverage for all public methods"

### Example 3: Performance Optimization

**Before (won't activate):**
"My app is slow"

**After (activates performance skills):**
"Analyze CPU usage patterns in this function and identify performance bottlenecks"

### Example 4: Database Operations

**Before (won't activate):**
"Fix my database"

**After (activates database optimizer):**
"Optimize these SQL queries and create indexes for better performance"

## Remember

**Skills are tools, not mind readers.** Give Claude clear instructions using the trigger phrases, and skills will activate reliably every time!

---

**For Developers:** See [SKILLS_SCHEMA_2025.md](SKILLS_SCHEMA_2025.md) for technical details on skill creation and the 2025 schema.

**For Plugin Authors:** Include clear trigger phrases in your skill descriptions to improve user experience!
