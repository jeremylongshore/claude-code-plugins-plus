# Claude Code Skills Reference Manual

**Version**: 2.4.0
**Last Updated**: 2025-12-19
**Author**: Intent Solutions (Jeremy Longshore)

---

## Table of Contents

1. [YAML Frontmatter Schema](#1-yaml-frontmatter-schema)
2. [Description Field Specification](#2-description-field-specification)
3. [Allowed Tools Reference](#3-allowed-tools-reference)
4. [Naming Conventions](#4-naming-conventions)
5. [Instruction Body Structure](#5-instruction-body-structure)
6. [Progressive Disclosure Patterns](#6-progressive-disclosure-patterns)
7. [Validation Rules](#7-validation-rules)
8. [Enterprise Extension Fields](#8-enterprise-extension-fields)
9. [Complete Templates](#9-complete-templates)
10. [Anti-Patterns to Avoid](#10-anti-patterns-to-avoid)

---

## 1. YAML Frontmatter Schema

### Anthropic Required Fields

```yaml
---
name: skill-name-kebab-case          # REQUIRED - max 64 chars
description: |                        # REQUIRED - max 1024 chars
  What this skill does. When to use it.
  Trigger phrases for discovery.
---
```

### Enterprise Required Fields

```yaml
---
name: skill-name-kebab-case
description: |
  Primary capability. Secondary features.
  Use when [scenarios]. Trigger with "[phrases]".
allowed-tools:                        # REQUIRED (Enterprise)
  - Read
  - Write
  - Bash
version: 1.0.0                        # REQUIRED (Enterprise) - semver
author: Name <email@domain.com>       # REQUIRED (Enterprise)
license: MIT                          # REQUIRED (Enterprise)
tags:                                 # RECOMMENDED
  - category
  - domain
---
```

### Complete Schema Reference

| Field | Type | Required | Max Length | Validation |
|-------|------|----------|------------|------------|
| `name` | string | Yes (Anthropic) | 64 chars | kebab-case, no XML, no reserved words |
| `description` | string | Yes (Anthropic) | 1024 chars | Non-empty, no XML tags |
| `allowed-tools` | array/CSV | Yes (Enterprise) | - | Valid tool names |
| `version` | string | Yes (Enterprise) | - | Semver format (X.Y.Z) |
| `author` | string | Yes (Enterprise) | - | Name <email> format |
| `license` | string | Yes (Enterprise) | - | Valid license (MIT, Apache-2.0, etc.) |
| `tags` | array | Recommended | - | Lowercase strings |

### Reserved Words (Cannot Use in Name)

- `anthropic`
- `claude`

---

## 2. Description Field Specification

### The Description Formula

```
[Action Verbs] + [Specific Capabilities] + [Use When] + [Trigger Phrases]
```

### Action Verbs Reference

| Category | Action Verbs |
|----------|-------------|
| **Data Operations** | Extract, analyze, parse, transform, convert, merge, split, validate, filter, aggregate |
| **Creation** | Generate, create, build, produce, synthesize, compose, scaffold, initialize |
| **Modification** | Edit, update, refactor, optimize, fix, enhance, migrate, patch, upgrade |
| **Analysis** | Review, audit, scan, inspect, diagnose, profile, assess, evaluate, benchmark |
| **Operations** | Deploy, execute, run, configure, install, setup, provision, orchestrate |
| **Documentation** | Document, explain, summarize, annotate, describe, catalog, index |
| **Testing** | Test, verify, validate, check, assert, measure, monitor |
| **Security** | Secure, encrypt, authenticate, authorize, protect, harden, sanitize |

### Description Patterns

**Pattern 1: Action-Focused (RECOMMENDED)**
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

**Pattern 3: Domain-Specific**
```yaml
description: |
  Analyze SQL query performance and suggest optimizations.
  Use for slow queries, missing indexes, N+1 problems, and query plan analysis.
  Trigger with "optimize query", "slow SQL", "query performance".
```

**Pattern 4: Multi-Capability**
```yaml
description: |
  Comprehensive Docker Compose management: generate configs, validate syntax, optimize services.
  Use when creating docker-compose.yaml, debugging container issues, or optimizing multi-service deployments.
  Trigger with "docker compose", "container orchestration", "multi-container".
```

### Good vs Bad Examples

| Quality | Example | Problem |
|---------|---------|---------|
| BAD | `Helps with documents` | Too vague, no triggers |
| BAD | `Processes data` | No specificity |
| BAD | `I can help you with PDFs` | First person |
| BAD | `You can use this for files` | Second person |
| GOOD | `Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.` | Specific, third person, has triggers |

### Critical Rules

1. **Always third person** - Never "I can help" or "You can use"
2. **Include file types** - .pdf, .xlsx, .yaml, .json, .ts
3. **Include domain keywords** - Kubernetes, SQL, Docker, Git
4. **Define boundaries** - What it cannot do
5. **Max 1024 characters**
6. **Include trigger phrases** - What users might say

---

## 3. Allowed Tools Reference

### Core Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `Read` | Read file contents | Read configuration files |
| `Write` | Create/overwrite files | Generate new files |
| `Edit` | Modify existing files | Update code |
| `Grep` | Search file contents | Find patterns |
| `Glob` | Find files by pattern | Locate files |
| `Bash` | Execute shell commands | Run scripts |
| `WebFetch` | Fetch web content | API calls |
| `WebSearch` | Search the web | Research |

### Tool Permission Categories

**Read-Only Analysis**
```yaml
allowed-tools:
  - Read
  - Grep
  - Glob
```

**Code Editing**
```yaml
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
```

**Web Research**
```yaml
allowed-tools:
  - Read
  - WebFetch
  - WebSearch
  - Grep
```

**Database Operations**
```yaml
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
```

**Testing**
```yaml
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
```

### Bash Tool Scoping

```yaml
# Full Bash access
allowed-tools:
  - Bash

# Scoped Bash (specific command categories)
allowed-tools:
  - Bash(git:*)      # Git commands only
  - Bash(npm:*)      # NPM commands only
  - Bash(docker:*)   # Docker commands only
```

### Tool Format Options

**Array Format (RECOMMENDED)**
```yaml
allowed-tools:
  - Read
  - Write
  - Bash
```

**CSV Format**
```yaml
allowed-tools: Read, Write, Bash
```

---

## 4. Naming Conventions

### Name Field Rules

| Rule | Requirement |
|------|-------------|
| Characters | Lowercase letters, numbers, hyphens only |
| Format | `kebab-case` |
| Max Length | 64 characters |
| Restrictions | No XML tags, no reserved words |

### Naming Patterns

**Gerund Form (RECOMMENDED)**
```
processing-pdfs
analyzing-spreadsheets
managing-databases
testing-code
```

**Noun Phrases**
```
pdf-processor
spreadsheet-analyzer
database-manager
code-tester
```

**Action-Oriented**
```
process-pdfs
analyze-spreadsheets
manage-database
test-code
```

### Bad Names to Avoid

| Name | Problem |
|------|---------|
| `helper` | Too vague |
| `utils` | Not descriptive |
| `tools` | Generic |
| `my-awesome-skill` | Not professional |
| `anthropic-helper` | Reserved word |
| `claude-tools` | Reserved word |
| `PDF_Processor` | Wrong case |
| `pdf processor` | Spaces not allowed |

---

## 5. Instruction Body Structure

### Standard Structure

```markdown
---
name: skill-name
description: |
  Description here.
allowed-tools: "Read, Write, Bash(git:*)"
version: 1.0.0
author: Name <email>
license: MIT
---

# Skill Name

Brief purpose statement (1-2 sentences).

## Overview

What this skill does, when to use it, key capabilities.
- Capability 1
- Capability 2
- Capability 3

## Prerequisites

- Required tool: `tool-name`
- Environment variable: `ENV_VAR`
- Dependency: `package-name`

## Instructions

### Step 1: Verb Action

Clear, imperative instructions.

```bash
command example
```

### Step 2: Verb Action

More instructions with code examples.

### Step 3: Verb Action

Final steps.

## Output

What artifacts this skill produces:
- File: `output.json`
- Report: Summary in terminal
- Modified: Updated configuration

## Error Handling

### Common Error 1

**Cause**: Description of cause
**Solution**: How to fix

### Common Error 2

**Cause**: Description
**Solution**: Fix steps

## Examples

### Example 1: Basic Usage

**Input**:
```
User request example
```

**Output**:
```
Expected result
```

### Example 2: Advanced Usage

More complex scenario.

## Resources

- [Official Docs](https://example.com)
- See `{baseDir}/reference.md` for details
```

### Body Length Guidelines

| Content | Max Lines | Notes |
|---------|-----------|-------|
| SKILL.md body | 500 lines | Split if longer |
| Quick start | 20-30 lines | Essential info only |
| Full reference | Separate file | Use progressive disclosure |

---

## 6. Progressive Disclosure Patterns

### Pattern 1: High-Level Guide with References

```markdown
# PDF Processing

## Quick Start

Extract text with pdfplumber:
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

## Advanced Features

**Form filling**: See [FORMS.md](FORMS.md) for complete guide
**API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
**Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
```

### Pattern 2: Domain-Specific Organization

```
skill-directory/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md (revenue metrics)
    ├── sales.md (pipeline data)
    ├── product.md (usage analytics)
    └── marketing.md (campaigns)
```

### Pattern 3: Conditional Details

```markdown
# Document Processing

## Creating Documents

Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing Documents

For simple edits, modify the XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

### Key Rules

1. **Keep references one level deep** - All reference files link from SKILL.md
2. **Add table of contents** - For files > 100 lines
3. **Use `{baseDir}`** - For portable file references

---

## 7. Validation Rules

### Field Validation

| Field | Validation |
|-------|------------|
| `name` | Non-empty, max 64 chars, kebab-case, no reserved words |
| `description` | Non-empty, max 1024 chars, no XML tags |
| `allowed-tools` | Valid tool names from known list |
| `version` | Semver format (X.Y.Z) |
| `author` | Non-empty, ideally `Name <email>` format |
| `license` | Valid SPDX license identifier |

### Content Validation

| Check | Rule |
|-------|------|
| Hardcoded paths | No `/tmp/`, `/home/user/`, absolute paths |
| Description quality | Must include action verbs |
| File references | Use `{baseDir}` for bundled files |
| Tool references | Must be in `allowed-tools` |

### Validator Script

```bash
# Validate all skills
python3 scripts/validate-skills-schema.py

# Validate specific directory
python3 scripts/validate-skills-schema.py plugins/devops/

# Fix enterprise fields
python3 scripts/fix-skills-enterprise.py
```

---

## 8. Enterprise Extension Fields

### Intent Solutions Standard

```yaml
version: 1.0.0                                    # Required
author: Jeremy Longshore <jeremy@intentsolutions.io>  # Required
license: MIT                                      # Required
tags:                                             # Recommended
  - category
  - domain
```

### Tag Taxonomy

**Primary Categories**
- `devops`, `security`, `testing`, `performance`
- `database`, `api`, `documentation`, `ai-ml`

**Domains**
- `kubernetes`, `docker`, `terraform`, `aws`, `gcp`, `azure`
- `python`, `typescript`, `javascript`, `rust`, `go`
- `postgresql`, `mongodb`, `redis`, `elasticsearch`

**Actions**
- `debugging`, `optimization`, `generation`, `analysis`
- `migration`, `deployment`, `monitoring`, `validation`

---

## 9. Complete Templates

### Basic Skill Template

```yaml
---
name: basic-skill-name
description: |
  Primary capability as action verb. Secondary features.
  Use when [2-3 specific scenarios].
  Trigger with "phrase 1", "phrase 2", "phrase 3".
allowed-tools:
  - Read
  - Grep
  - Glob
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
tags:
  - category
  - domain
---

# Basic Skill Name

Brief purpose statement.

## Overview

What this skill does and when to use it.

## Instructions

### Step 1: Analyze

Read and understand the input.

### Step 2: Process

Apply the skill logic.

### Step 3: Output

Return results to user.

## Examples

### Example 1: Basic Usage

Input and expected output.
```

### Advanced Skill Template (with scripts)

```yaml
---
name: advanced-skill-name
description: |
  Comprehensive toolkit for [domain]. Analyze, transform, and generate.
  Use when working with [file types] or when user needs [capabilities].
  Trigger with "analyze [domain]", "generate [output]", "optimize [target]".
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
tags:
  - devops
  - automation
---

# Advanced Skill Name

Comprehensive description of purpose.

## Overview

- Capability 1: Description
- Capability 2: Description
- Capability 3: Description

## Prerequisites

- Tool: `required-cli-tool`
- Package: `required-package`

## Workflow

### Phase 1: Analysis

1. Run analysis script:
```bash
python {baseDir}/scripts/analyze.py input.file
```

2. Review output in `analysis.json`

### Phase 2: Transformation

1. Apply transformations:
```bash
python {baseDir}/scripts/transform.py analysis.json
```

### Phase 3: Validation

1. Validate results:
```bash
python {baseDir}/scripts/validate.py output.file
```

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `analyze.py` | Initial analysis |
| `transform.py` | Apply changes |
| `validate.py` | Verify output |

## Error Handling

### Error: Invalid Input

**Cause**: Input file malformed
**Solution**: Validate input format first

## Examples

### Example 1: Full Workflow

Complete example with input, commands, and output.
```

### Read-Only Analysis Template

```yaml
---
name: analysis-skill-name
description: |
  Analyze and report on [domain]. Scan, inspect, and assess.
  Use when reviewing [targets] or auditing [systems].
  Trigger with "analyze [domain]", "audit [target]", "review [subject]".
allowed-tools:
  - Read
  - Grep
  - Glob
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
tags:
  - analysis
  - audit
---

# Analysis Skill Name

Read-only analysis and reporting.

## Overview

This skill analyzes without modifying:
- Scans for patterns
- Identifies issues
- Generates reports

## Analysis Steps

### Step 1: Gather Data

Read relevant files and configurations.

### Step 2: Analyze Patterns

Search for specific patterns and issues.

### Step 3: Generate Report

Produce summary with findings.

## Output Format

```
## Analysis Report

### Summary
- Total files scanned: X
- Issues found: Y
- Recommendations: Z

### Details
...
```
```

---

## 10. Anti-Patterns to Avoid

### Description Anti-Patterns

| Anti-Pattern | Example | Fix |
|--------------|---------|-----|
| First person | "I can help you with PDFs" | "Extract text from PDF files" |
| Second person | "You can use this for..." | "Use when working with..." |
| Too vague | "Helps with documents" | "Extract, merge, and fill PDF forms" |
| No triggers | "PDF processing tool" | Add "Use when... Trigger with..." |
| Too long | >1024 characters | Condense to essentials |

### Structure Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Deep nesting | References 3+ levels deep | Keep 1 level deep |
| No ToC | Long files hard to navigate | Add table of contents |
| Windows paths | `scripts\helper.py` | Use forward slashes |
| Absolute paths | `/home/user/file.txt` | Use `{baseDir}` |
| Magic numbers | `TIMEOUT = 47` | Document why this value |

### Tool Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| `Bash(*)` | Invalid wildcard | Use `Bash` or `Bash(cmd:*)` |
| Overly permissive | All tools for read-only skill | Limit to needed tools |
| Missing tools | Uses Bash but not listed | Add to allowed-tools |

### Content Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Assumes installation | "Use the pdf library" | "Install with `pip install pypdf`" |
| Time-sensitive | "Before August 2025, use old API" | Use "old patterns" section |
| Inconsistent terms | Mix "field", "box", "element" | Pick one, use consistently |
| Too many options | "Use pypdf, or pdfplumber, or..." | Provide default, mention alternatives |

---

## Appendix A: Quick Reference Card

```yaml
# SKILL.md Quick Reference

---
name: kebab-case-name                 # Max 64 chars, required
description: |                        # Max 1024 chars, required
  [Action verb] [capability]. [More features].
  Use when [scenarios].
  Trigger with "[phrase1]", "[phrase2]".
allowed-tools:                        # Enterprise required
  - Read
  - Write
  - Bash
version: 1.0.0                        # Enterprise required
author: Name <email>                  # Enterprise required
license: MIT                          # Enterprise required
tags: [category, domain]              # Recommended
---

# Skill Name

## Overview
What it does.

## Instructions
### Step 1: Verb
Instructions.

## Examples
### Basic Usage
Example.
```

---

## Appendix B: Validation Checklist

- [ ] Name is kebab-case, max 64 chars
- [ ] Description is max 1024 chars
- [ ] Description uses action verbs
- [ ] Description includes trigger phrases
- [ ] Description is third person
- [ ] allowed-tools lists only needed tools
- [ ] version follows semver (X.Y.Z)
- [ ] author is `Name <email>` format
- [ ] license is valid SPDX identifier
- [ ] No hardcoded paths
- [ ] File references use `{baseDir}`
- [ ] Body under 500 lines
- [ ] Complex content in separate files

---

**Document Version**: 2.4.0
**Maintained By**: Intent Solutions
**Source**: Anthropic Official Documentation + Enterprise Extensions
