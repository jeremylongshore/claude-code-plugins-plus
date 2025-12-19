# Planned Skills - 500 Standalone Skills Initiative

**Purpose**: Planning directory for creating 500 standalone Claude Code skills.

**Location**: `planned-skills/`

---

## Contents

### SKILLS-STANDARD-COMPLETE.md (65KB)

**The ONLY document you need** for writing/auditing Claude Skills.

This comprehensive reference combines:
1. **Master Skills Standard** (Anthropic official spec)
2. **Appendix A**: Frontmatter Schema Quick Reference
3. **Appendix B**: Authoring Guide & Patterns
4. **Appendix C**: Strategy Guide

**Use this for**:
- Complete SKILL.md structure specification
- YAML frontmatter fields (name, description, allowed-tools, version, author, license)
- Instruction-body best practices
- Security & safety guidance
- Production-readiness checklist (18-point checklist)
- Canonical SKILL.md template
- Description formula & patterns
- Validation rules with examples

---

## 500 Skills Initiative

### Current State
- **241 skills** exist (embedded in plugins)
- **259 more skills** needed to reach 500
- All existing skills now enterprise-compliant

### Enterprise Standard Fields (Required)

| Field | Type | Required | Example |
|-------|------|----------|---------|
| `name` | string | Yes (Anthropic) | `kubernetes-pod-debugger` |
| `description` | string | Yes (Anthropic) | Clear, with trigger phrases |
| `allowed-tools` | CSV/list | Yes (Enterprise) | `Read, Write, Bash` |
| `version` | semver | Yes (Enterprise) | `1.0.0` |
| `author` | string | Yes (Enterprise) | `Jeremy Longshore <jeremy@intentsolutions.io>` |
| `license` | string | Yes (Enterprise) | `MIT` |
| `tags` | array | Recommended | `["devops", "kubernetes"]` |

### Skill Categories to Create

| Category | Count | Examples |
|----------|-------|----------|
| DevOps Automation | 40 | CI/CD, deployment, infrastructure |
| Security & Compliance | 35 | Auditing, scanning, hardening |
| Database Operations | 30 | Query optimization, migrations |
| API Development | 25 | Design, testing, documentation |
| Code Quality | 25 | Review, refactoring, standards |
| Testing & QA | 25 | Unit, integration, e2e |
| Documentation | 20 | Technical writing, API docs |
| Performance | 20 | Profiling, optimization, caching |
| AI/ML Ops | 20 | Model training, serving |
| Cloud Architecture | 19 | AWS, GCP, Azure patterns |
| **TOTAL** | **259** | |

---

## Directory Structure (Planned)

```
planned-skills/
├── README.md                          # This file
├── SKILLS-STANDARD-COMPLETE.md        # Master specification
├── skill-definitions/                 # Skill definition files
│   ├── devops-skills.yaml            # DevOps skill definitions
│   ├── security-skills.yaml          # Security skill definitions
│   ├── database-skills.yaml          # Database skill definitions
│   └── ...                           # Other categories
├── templates/                         # Skill templates
│   ├── basic-skill.md                # Basic skill template
│   ├── advanced-skill.md             # Advanced with scripts
│   └── read-only-skill.md            # Read-only analysis skill
└── generated/                         # Generated skills (staging)
    └── batch-001/                    # First batch of generated skills
```

---

## Validation Scripts

Located in `scripts/`:

- `validate-skills-schema.py` - Validates against Anthropic + Enterprise spec
- `fix-skills-enterprise.py` - Batch fixes missing enterprise fields
- `audit-skills-quality.py` - Quality scoring and analysis

### Run Validation

```bash
# Full validation
python3 scripts/validate-skills-schema.py

# Fix missing enterprise fields
python3 scripts/fix-skills-enterprise.py

# Quality audit
python3 scripts/audit-skills-quality.py
```

---

## Description Writing Guide (Critical for Discovery)

The `description` field is **the most important field** for skill activation. Claude uses it to decide when to invoke your skill from potentially 100+ available skills.

### The Description Formula

```
[Action Verbs] + [Specific Capabilities] + [Use When] + [Trigger Phrases]
```

**Max Length**: 1024 characters

### Action Verbs (Use These)

| Category | Action Verbs |
|----------|-------------|
| Data | Extract, analyze, parse, transform, convert, merge, split, validate |
| Creation | Generate, create, build, produce, synthesize, compose |
| Modification | Edit, update, refactor, optimize, fix, enhance, migrate |
| Analysis | Review, audit, scan, inspect, diagnose, profile, assess |
| Operations | Deploy, execute, run, configure, install, setup, provision |
| Documentation | Document, explain, summarize, annotate, describe |

### Description Structure

**Pattern 1: Action-focused (Recommended)**
```yaml
description: |
  Extract text and tables from PDFs, fill forms, merge documents.
  Use when working with PDF files or when user mentions PDFs, forms, or document extraction.
```

**Pattern 2: Capability + Trigger**
```yaml
description: |
  Kubernetes pod debugging and troubleshooting toolkit.
  Use when pods crash, fail to start, or exhibit unexpected behavior.
  Trigger with "debug pod", "pod failing", "container crash".
```

**Pattern 3: Domain-specific**
```yaml
description: |
  Analyze SQL query performance and suggest optimizations.
  Use for slow queries, missing indexes, N+1 problems, and query plan analysis.
  Trigger with "optimize query", "slow SQL", "query performance".
```

### Good vs Bad Examples

**BAD: Too Vague**
```yaml
description: Helps with documents
description: Processes data
description: Does stuff with files
```

**GOOD: Specific with Triggers**
```yaml
description: |
  Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

**BAD: No Activation Context**
```yaml
description: For data analysis
```

**GOOD: Clear When to Activate**
```yaml
description: |
  Analyze Excel spreadsheets, create pivot tables, generate charts.
  Use when working with Excel files, spreadsheets, or .xlsx files.
  Trigger with "analyze spreadsheet", "excel report", "pivot table".
```

### Enterprise Description Template

```yaml
description: |
  [Primary capability as action verb]. [Secondary capabilities].
  Use when [2-3 specific scenarios].
  Trigger with "[phrase1]", "[phrase2]", "[phrase3]".
```

### Key Rules

1. **Always write in third person** (not "I can help" or "You can use")
2. **Include specific file types** (.pdf, .xlsx, .yaml)
3. **Include domain keywords** (Kubernetes, SQL, Docker)
4. **Define boundaries** (what it can NOT do)
5. **Keep under 1024 characters**

---

## Quick Reference: SKILL.md Template

```yaml
---
name: skill-name-kebab-case
description: |
  Primary capabilities as action verbs. Secondary features.
  Use when [3-4 trigger scenarios].
  Trigger with "phrase 1", "phrase 2", "phrase 3".
allowed-tools:
  - Read
  - Write
  - Bash
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
tags:
  - category1
  - category2
---

# Skill Name

Brief purpose statement.

## Overview

What this skill does, when to use it, key capabilities.

## Prerequisites

Required tools, APIs, environment variables.

## Instructions

### Step 1: Action Verb

Clear, imperative instructions.

### Step 2: Action Verb

More instructions.

## Output

What artifacts this skill produces.

## Error Handling

Common failures and solutions.

## Examples

### Example 1: Basic Scenario

Input and expected output.

## Resources

Links to bundled files using `{baseDir}`.
```

---

## External References

- [Anthropic Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Lee Han Chung Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Anthropic Engineering Blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

---

**Last Updated**: 2025-12-19
**Maintained By**: Intent Solutions (Jeremy Longshore)
**Goal**: 500 enterprise-grade standalone skills
