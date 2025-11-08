# Claude Code Skills Schema - 2025 Specification

**Last Updated:** November 8, 2025
**Status:** MIGRATION REQUIRED
**Priority:** HIGH

## Current State

**CRITICAL:** Our marketplace is behind the latest Claude Code Skills schema. Only 4% of our skills use the recommended 2025 schema enhancements.

### Statistics
- **Total Skills:** 175 SKILL.md files
- **With `allowed-tools` field:** 7 (4%)
- **With `version` field:** 5 (3%)
- **Needing Update:** 168 skills (96%)

## 2025 Official Schema

### Required Fields

```yaml
---
name: skill-name
description: Brief description of what the skill does and when to use it
---
```

### Recommended Fields (NEW)

```yaml
---
name: skill-name
description: Brief description of what the skill does and when to use it
allowed-tools: Read, Write, Edit, Grep, Bash  # Recommended - limits tool access
version: 1.0.0  # Recommended - version tracking
---
```

## Field Specifications

### `name` (Required)
- **Format:** lowercase letters, numbers, hyphens only
- **Max Length:** 64 characters
- **Example:** `monitoring-cpu-usage`

### `description` (Required)
- **Format:** Clear description including WHAT and WHEN
- **Max Length:** 1024 characters
- **Best Practice:** Include trigger phrases for auto-activation
- **Example:**
  ```yaml
  description: |
    This skill monitors CPU usage patterns. Use when you need to
    "analyze CPU performance" or "detect CPU bottlenecks".
  ```

### `allowed-tools` (Optional but Recommended)
- **Purpose:** Security and performance - limits which tools Claude can use
- **Format:** Comma-separated list of tool names
- **Benefits:**
  - **Security:** Prevents unintended tool usage
  - **Performance:** Reduces token usage
  - **Clarity:** Makes capabilities explicit

### `version` (Optional but Recommended)
- **Purpose:** Track skill evolution over time
- **Format:** Semantic versioning (x.y.z)
- **Example:** `version: 1.0.0`

## Tool Categorization Guide

### Read-Only Analysis
Use for skills that only analyze without modifying:
```yaml
allowed-tools: Read, Grep, Glob, Bash
```

**Example Skills:** CPU monitoring, code analysis, security scanning

### Code Editing
Use for skills that create or modify files:
```yaml
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
```

**Example Skills:** Code generators, refactoring tools, file creators

### Web Research
Use for skills that fetch online content:
```yaml
allowed-tools: Read, WebFetch, WebSearch, Grep
```

**Example Skills:** Documentation lookup, research tools, API discovery

### Database Operations
Use for skills working with databases:
```yaml
allowed-tools: Read, Write, Bash, Grep
```

**Example Skills:** Query builders, migration tools, schema designers

### Testing
Use for skills running tests:
```yaml
allowed-tools: Read, Bash, Grep, Glob
```

**Example Skills:** Test runners, coverage analyzers, test generators

## Migration Status

### ✅ Already Compliant (7 skills)
- skills-powerkit/* (5 skills)
- pi-pathfinder
- overnight-dev

### ⚠️ Needs Update (168 skills)
All other skills in the marketplace

## Migration Plan

See detailed implementation plan in private documentation.

**Target Completion:** 3-4 weeks
**Approach:** Automated migration with manual validation
**Impact:** Zero breaking changes (backward compatible)

## Why This Matters

1. **User Trust:** Explicit permissions build confidence
2. **Performance:** Tool restrictions reduce overhead
3. **Marketplace Positioning:** Shows active maintenance
4. **Best Practices:** Aligns with Anthropic standards
5. **Future-Proofing:** Ready for next Claude Code updates

## For Contributors

When creating new skills, always include all four fields:

```yaml
---
name: my-new-skill
description: |
  Clear description of what this does and when to use it.
  Include trigger phrases like "analyze code quality".
allowed-tools: Read, Grep, Glob, Bash
version: 1.0.0
---
```

## Available Tools

Common tools you can specify in `allowed-tools`:
- `Read` - Read files
- `Write` - Create new files
- `Edit` - Modify existing files
- `Grep` - Search file contents
- `Glob` - Find files by pattern
- `Bash` - Execute shell commands
- `WebFetch` - Fetch web pages
- `WebSearch` - Search the web
- `Task` - Launch sub-agents

**Principle:** Use the minimum tools necessary for the skill's purpose.

## References

- [Claude Code Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- See CLAUDE.md for repository-specific guidelines

---

**Action Required:** Maintainers should prioritize updating skills to 2025 schema for competitive positioning and user trust.
