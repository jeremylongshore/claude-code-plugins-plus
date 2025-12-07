# Claude Skills Standard

**Document ID**: 6767-b-SPEC-MASTER-claude-skills-standard
**Version**: 1.0.0
**Created**: 2025-12-06
**Applies to**: claude-code-plugins-plus repository

---

## What Is a Skill?

A Claude Skill is a **prompt-based capability package** that transforms Claude's behavior when activated. Skills are NOT executable plugins—they inject context and instructions.

**Key insight**: Skills live in a meta-tool called `Skill`. Claude reads descriptions and decides when to activate.

---

## Skill Structure

```
skill-name/
├── SKILL.md              # Required: Instructions + YAML frontmatter
├── scripts/              # Optional: Python/Bash helpers
├── references/           # Optional: Docs loaded into context
└── assets/               # Optional: Templates, configs
```

**IMPORTANT**: Folder name must match the `name` field exactly.

---

## SKILL.md Schema

### Required Frontmatter

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Lowercase + hyphens, matches folder name |
| `description` | string | What + when + trigger phrases (third person) |

### Recommended Frontmatter

| Field | Type | Description |
|-------|------|-------------|
| `allowed-tools` | CSV string | Pre-approved tools during execution |
| `version` | string | Semver (1.0.0) |

### Optional Frontmatter

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Model override (sonnet, opus, haiku, inherit) |
| `mode` | boolean | Display as "mode command" in UI |
| `disable-model-invocation` | boolean | Manual invocation only |

### Forbidden Fields

Do not use: `author`, `priority`, `audience`, `when_to_use`, `license`

---

## Example SKILL.md

```yaml
---
name: code-reviewer
description: >
  Analyze code for bugs, security issues, and style violations.
  Use when reviewing PRs, checking diffs, or auditing code quality.
  Trigger with "review this code", "check for issues".
allowed-tools: "Read,Grep,Glob"
version: "1.0.0"
---

# Code Reviewer

Analyze code changes and generate structured review feedback.

## Overview

This skill examines code for bugs, security vulnerabilities,
performance issues, and style violations.

## Prerequisites

- Git repository with code to review
- Read access to codebase

## Instructions

### Step 1: Get Context

Read the files to be reviewed using appropriate tools.

### Step 2: Analyze Code

Check for:
- Logic errors and edge cases
- Security vulnerabilities
- Performance problems
- Style violations

### Step 3: Generate Report

Produce structured feedback with severity levels.

## Output

- Markdown review with categorized findings
- Clear recommendation (APPROVE, REQUEST_CHANGES)

## Error Handling

1. **Error**: File not found
   **Solution**: Verify file path is correct

2. **Error**: Binary file
   **Solution**: Skip binary files, note for manual review

## Examples

### Example 1: Simple Review

**Input**: "Review src/auth.ts"

**Output**:
```markdown
## Review: src/auth.ts

### Critical
- Line 45: SQL injection vulnerability

### Suggestions
- Line 78: Consider extracting to helper function

### Recommendation
REQUEST_CHANGES
```
```

---

## Description Formula

```
[Primary capabilities]. [Secondary features].
Use when [scenarios]. Trigger with "[phrases]".
```

**Good**:
```yaml
description: >
  Extract text from PDFs, fill forms, merge documents.
  Use when working with PDF files or document extraction.
  Trigger with "process PDF", "extract from PDF".
```

**Bad**:
```yaml
description: Helps with documents    # Too vague
description: I process your PDFs    # Wrong voice (use third person)
```

---

## allowed-tools Examples

```yaml
# Read-only operations
allowed-tools: "Read,Glob,Grep"

# File operations
allowed-tools: "Read,Write,Edit"

# Scoped bash commands
allowed-tools: "Bash(git:*),Read,Grep"

# Multiple scoped commands
allowed-tools: "Bash(npm:*),Bash(npx:*),Read,Write"
```

**Principle**: Grant ONLY tools the skill actually needs.

---

## Content Guidelines

| Guideline | Requirement |
|-----------|-------------|
| Size | SKILL.md body under 500 lines |
| Voice | Third person in description, imperative in instructions |
| Paths | Use `{baseDir}` variable, never hardcode |
| Examples | 2-3 concrete examples with input/output |
| Errors | 4+ common failures documented |

---

## Validation Checklist

- [ ] `skill-name/SKILL.md` structure (not flat .md file)
- [ ] `name` matches folder name (lowercase + hyphens)
- [ ] `description` is non-empty, third person voice
- [ ] `allowed-tools` is CSV string (not array)
- [ ] `version` follows semver
- [ ] No forbidden fields (author, priority, etc.)
- [ ] Body under 500 lines
- [ ] Uses `{baseDir}` for paths

---

## Discovery Locations

| Location | Scope | Priority |
|----------|-------|----------|
| `~/.claude/skills/` | Personal (all projects) | 1 (lowest) |
| `.claude/skills/` | Project-specific | 2 |
| Plugin `skills/` directory | Plugin-bundled | 3 |
| Built-in skills | Platform-provided | 4 (highest) |

Later sources override earlier when names conflict.

---

## References

- Anthropic Docs: https://docs.anthropic.com/en/docs/claude-code
- Claude Code GitHub: https://github.com/anthropics/claude-code
