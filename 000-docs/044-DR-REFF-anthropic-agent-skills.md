# Anthropic Agent Skills - Complete Reference Guide
**Compiled from Official Anthropic Documentation**
**Date:** 2025-10-19
**Purpose:** Master reference for automated plugin enhancement system

---

## Table of Contents
1. [Official Skills Specification](#official-skills-specification)
2. [Skill Creation Process](#skill-creation-process)
3. [SKILL.md Format](#skillmd-format)
4. [Bundled Resources](#bundled-resources)
5. [Progressive Disclosure](#progressive-disclosure)
6. [Writing Style Guide](#writing-style-guide)
7. [Quality Checklist](#quality-checklist)
8. [Real Examples Analysis](#real-examples-analysis)

---

## Official Skills Specification
**Source:** github.com/anthropics/skills/agent_skills_spec.md

### Core Definition
A skill is a folder of instructions, scripts, and resources that agents can discover and load dynamically to perform better at specific tasks.

### Required Structure
```
my-skill/
  - SKILL.md (REQUIRED)
```

### Extended Structure (Recommended)
```
my-skill/
├── SKILL.md                    # Required entrypoint
├── scripts/                    # Optional: Executable utilities
│   ├── script1.py
│   └── script2.sh
├── references/                 # Optional: Documentation
│   ├── api_docs.md
│   └── schemas.md
└── assets/                     # Optional: Output resources
    ├── templates/
    └── fonts/
```

### SKILL.md Frontmatter Specification

**Required Fields:**
```yaml
---
name: skill-name               # REQUIRED: hyphen-case lowercase
description: |                 # REQUIRED: Multi-line description
  What the skill does and when Claude should use it.
  Include trigger phrases and use cases.
---
```

**Optional Fields:**
```yaml
---
name: skill-name
description: Multi-line description
license: "MIT"                 # Optional: License info
allowed-tools:                 # Optional: Claude Code only
  - Read
  - Write
  - Bash
metadata:                      # Optional: Custom key-value
  author: "Name"
  version: "1.0.0"
  category: "productivity"
---
```

### Naming Conventions

**Name Field Rules:**
- MUST use hyphen-case (not camelCase, PascalCase, or snake_case)
- MUST be lowercase
- MUST only contain Unicode alphanumeric + hyphen
- MUST match the directory name containing SKILL.md

**Examples:**
- ✅ `pdf-editor`
- ✅ `web-scraper-pro`
- ✅ `database-optimizer`
- ❌ `pdfEditor` (camelCase)
- ❌ `PDF_Editor` (snake_case with caps)
- ❌ `pdf editor` (spaces)

### Description Field Requirements

The description determines when Claude activates the skill. Must include:

1. **What it does** (capability statement)
2. **When to use it** (trigger conditions)
3. **Key features** (differentiators)

**Good Description Example:**
```yaml
description: |
  Comprehensive PDF manipulation toolkit for extracting text and tables,
  creating new PDFs, merging/splitting documents, and handling forms.
  Use when Claude needs to fill in PDF forms or programmatically process,
  generate, or analyze PDF documents at scale.
```

**Bad Description Example:**
```yaml
description: "Helps with PDFs"  # Too vague, no triggers
```

### Markdown Body Requirements

**No restrictions** - Free-form markdown content with these recommendations:

1. **Structure:** Use clear headings (##, ###)
2. **Examples:** Include code examples
3. **Instructions:** Provide step-by-step workflows
4. **References:** Point to bundled resources when applicable

---

## Skill Creation Process
**Source:** github.com/anthropics/skills/skill-creator/SKILL.md

### Step-by-Step Workflow

#### Step 1: Understanding the Skill with Concrete Examples

**Goal:** Clearly understand concrete examples of how the skill will be used

**Approach:**
- Gather direct user examples OR
- Generate examples and validate with user feedback

**Questions to Ask:**
- "What functionality should the skill support?"
- "Can you give examples of how this would be used?"
- "What would a user say to trigger this skill?"
- "Are there other use cases I'm missing?"

**Output:** Clear sense of the functionality the skill should support

#### Step 2: Planning the Reusable Skill Contents

**Goal:** Identify scripts, references, and assets needed

**Process:**
1. For each concrete example, consider execution from scratch
2. Identify what resources would help if doing this repeatedly

**Examples:**

**PDF Rotation Skill:**
- Observation: Rotating PDFs requires rewriting same code each time
- Resource: `scripts/rotate_pdf.py` for deterministic rotation

**Frontend Builder Skill:**
- Observation: Every webapp needs same boilerplate HTML/React
- Resource: `assets/hello-world/` template with boilerplate

**BigQuery Skill:**
- Observation: Querying requires re-discovering table schemas each time
- Resource: `references/schema.md` documenting all tables

**Output:** List of scripts, references, and assets to include

#### Step 3: Initializing the Skill

**Tool:** Use `init_skill.py` script (Anthropic provides this)

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

**What it creates:**
- Skill directory at specified path
- SKILL.md template with proper frontmatter
- Example `scripts/`, `references/`, `assets/` directories
- Placeholder files in each directory

**Next:** Customize or delete generated files as needed

#### Step 4: Edit the Skill

**Focus:** Create content for another instance of Claude to use

##### Start with Bundled Resources

1. Create `scripts/`, `references/`, `assets/` files identified in Step 2
2. May require user input (brand assets, templates, documentation)
3. Delete unused example directories

##### Update SKILL.md

**Writing Style Rules:**
- ✅ Use **imperative/infinitive form** (verb-first instructions)
- ✅ "To accomplish X, do Y"
- ❌ NO second person ("You should do X")
- ✅ Objective, instructional language

**Questions to Answer:**
1. What is the purpose of the skill? (2-3 sentences)
2. When should the skill be used? (trigger conditions)
3. How should Claude use the skill? (reference bundled resources)

#### Step 5: Packaging a Skill

**Tool:** Use `package_skill.py` script

```bash
scripts/package_skill.py <path/to/skill-folder>
scripts/package_skill.py <path/to/skill-folder> ./dist  # Custom output
```

**What it does:**
1. **Validates:**
   - YAML frontmatter format
   - Required fields (name, description)
   - Naming conventions
   - Directory structure
   - Description completeness

2. **Packages:**
   - Creates `my-skill.zip`
   - Includes all files
   - Maintains directory structure

**On Failure:** Reports errors, exits without package. Fix and retry.

#### Step 6: Iterate

**Workflow:**
1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify SKILL.md or bundled resource updates needed
4. Implement changes
5. Test again

---

## SKILL.md Format

### Recommended Content Structure

```markdown
---
name: skill-name
description: |
  Multi-line description with triggers
---

# Skill Name

## Overview
[2-3 sentence high-level description]

## Core Capabilities
- Capability 1
- Capability 2
- Capability 3

## Workflow

### Phase 1: [Phase Name]
To accomplish [goal]:

1. **Step 1:** [Detailed instruction]
   ```code
   # Example
   ```

2. **Step 2:** [Detailed instruction]

### Phase 2: [Phase Name]
[Continue...]

## Using Bundled Resources

### Scripts
To automate [task]:
```bash
./scripts/automation.py --option value
```

### References
For detailed information on [topic], load:
- [Reference Name](./references/guide.md)

### Assets
Available templates:
- `assets/template.html` - [Description]

## Examples

### Example 1: [Scenario Name]
User request: "[Example request]"

Workflow:
1. [Step with output]
2. [Step with output]
3. [Result]

### Example 2: [Scenario Name]
[Another complete example]

## Best Practices
- Practice 1
- Practice 2

## Troubleshooting

**Issue:** [Problem description]
**Solution:** [Fix]

## Integration
How this skill works with other tools/skills
```

### Target Metrics

Based on Anthropic's actual skills:

- **Size:** 8,000-15,000 bytes
- **Code Examples:** 10-20 examples
- **Workflow Phases:** 4-6 detailed phases
- **Examples:** 3-5 complete scenarios
- **Sections:** 8-12 major sections

---

## Bundled Resources

### Scripts Directory (`scripts/`)

**Purpose:** Executable code for deterministic operations

**When to Include:**
- Code being rewritten repeatedly
- Deterministic reliability needed
- Token efficiency important

**Benefits:**
- May execute without loading to context
- Ensures consistency
- Saves tokens

**Examples from Anthropic:**
- `scripts/init_skill.py` - Generate skill templates
- `scripts/package_skill.py` - Validate and package skills
- `scripts/quick_validate.py` - Fast validation checks
- `scripts/rotate_pdf.py` - PDF rotation utility

**Best Practices:**
- Make scripts executable (`chmod +x`)
- Include shebang line (`#!/usr/bin/env python3`)
- Add usage documentation in docstrings
- Handle errors gracefully
- Support `--help` flag

### References Directory (`references/`)

**Purpose:** Documentation loaded into context as needed

**When to Include:**
- Database schemas
- API documentation
- Domain knowledge
- Company policies
- Detailed workflow guides

**Benefits:**
- Keeps SKILL.md lean
- Loaded only when Claude determines it's needed
- No size limits

**Examples from Anthropic:**
- `references/mcp_best_practices.md` - MCP guidelines
- `references/python_mcp_server.md` - Python patterns
- `references/node_mcp_server.md` - TypeScript patterns
- `references/schema.md` - Database schemas
- `references/api_docs.md` - API specifications

**Best Practices:**
- Avoid duplication with SKILL.md
- For large files (>10k words), include grep patterns in SKILL.md
- Use descriptive filenames
- Add table of contents for long docs
- Include examples and code snippets

### Assets Directory (`assets/`)

**Purpose:** Files used in output (not loaded to context)

**When to Include:**
- Templates (HTML, React, documents)
- Images, icons, fonts
- Boilerplate code
- Sample documents to copy/modify

**Benefits:**
- Separates output resources from documentation
- Enables file usage without context loading
- Supports rich skill capabilities

**Examples from Anthropic:**
- `assets/logo.png` - Brand assets
- `assets/slides.pptx` - PowerPoint templates
- `assets/hello-world/` - HTML/React boilerplate
- `assets/font.ttf` - Typography files
- `assets/templates/` - Document templates

**Best Practices:**
- Organize by type (templates/, images/, fonts/)
- Use standard formats
- Keep file sizes reasonable
- Include README explaining assets
- License assets appropriately

---

## Progressive Disclosure

### Three-Level Loading System

**Goal:** Manage context efficiently

#### Level 1: Metadata (Always in Context)
- `name` and `description` fields
- ~100 words
- Used for skill discovery and triggering
- Always loaded

#### Level 2: SKILL.md Body (Loaded When Triggered)
- Full markdown content
- Target: <5k words
- Procedural instructions
- References to bundled resources
- Loaded when skill activates

#### Level 3: Bundled Resources (Loaded As Needed)
- `scripts/` - May execute without loading
- `references/` - Loaded when Claude determines needed
- `assets/` - Used in output, not loaded to context
- Unlimited total size*

*Scripts can be executed without reading into context window

### Implementation Strategy

**SKILL.md should:**
1. Provide high-level workflow
2. Reference detailed docs in `references/`
3. Point to scripts for automation
4. Mention available assets

**Example:**
```markdown
## Detailed Schema Information

For complete table schemas and relationships, load:
- [PostgreSQL Schema](./references/postgres_schema.md)
- [MongoDB Collections](./references/mongo_schema.md)

To analyze query performance, use:
```bash
./scripts/analyze_explain.py --query "SELECT * FROM users"
```
```

### Benefits

1. **Token Efficiency:** Only load what's needed
2. **Scalability:** No practical limit on total content
3. **Performance:** Faster skill activation
4. **Flexibility:** Claude decides what to load

---

## Writing Style Guide

### Imperative/Infinitive Form (REQUIRED)

**Rule:** Use verb-first instructions, not second person

**Correct Examples:**
- ✅ "To accomplish X, do Y"
- ✅ "Load and read the following reference files"
- ✅ "Create a comprehensive implementation plan"
- ✅ "For detailed information, consult the schema guide"

**Incorrect Examples:**
- ❌ "You should do X"
- ❌ "If you need to do X"
- ❌ "You can try Y"
- ❌ "Make sure you do Z"

### Objective, Instructional Language

**Good:**
```markdown
## Coverage Validation

To check coverage meets requirements:

1. Run test suite with coverage flag
2. Parse coverage report
3. Compare against threshold
4. Exit with error if below minimum
```

**Bad:**
```markdown
## Coverage Validation

You should check if your coverage is good enough by running
tests. If you get low coverage, you might want to add more tests.
```

### Third-Person Descriptions

**In frontmatter description:**
- ✅ "This skill should be used when..."
- ✅ "Activates when the user requests..."
- ❌ "Use this skill when you..."

### Clear Action Directives

**Good:**
```markdown
Execute the validation script:
```bash
./scripts/validate.sh --strict
```

Review output for errors. Fix any issues before proceeding.
```

**Bad:**
```markdown
You can run the validation script if you want. It might help.
```

---

## Quality Checklist

### Minimal Valid Skill ✅
- [ ] SKILL.md file exists
- [ ] Frontmatter has `name` field (hyphen-case)
- [ ] Frontmatter has `description` field (multi-line with triggers)
- [ ] Markdown body has some instructional content
- [ ] Name matches directory name

### Good Skill ⭐⭐⭐
- [ ] All minimal requirements
- [ ] SKILL.md is 3,000+ bytes
- [ ] Uses imperative/infinitive writing style
- [ ] Has 3-5 code examples
- [ ] Has structured workflow with phases
- [ ] Includes 1-2 complete usage examples
- [ ] Has troubleshooting section

### Excellent Skill ⭐⭐⭐⭐⭐
- [ ] All good skill requirements
- [ ] SKILL.md is 8,000+ bytes
- [ ] Has bundled resources (scripts, references, or assets)
- [ ] Has 10-15 code examples
- [ ] Has 4-6 detailed workflow phases
- [ ] Has 3-5 complete usage examples with outputs
- [ ] Implements progressive disclosure
- [ ] References bundled resources in SKILL.md
- [ ] Has comprehensive troubleshooting
- [ ] Includes integration notes

---

## Real Examples Analysis

### Example 1: skill-creator (Anthropic Official)

**Stats:**
- Size: 11,547 bytes
- Bundled scripts: 3 (init, package, validate)
- Code examples: 8
- Workflow phases: 6
- Complete examples: 5

**Structure:**
```markdown
# Skill Creator

## About Skills
[Conceptual overview]

## Skill Creation Process

### Step 1: Understanding the Skill with Concrete Examples
[Detailed workflow]

### Step 2: Planning the Reusable Skill Contents
[Implementation guidance]

### Step 3: Initializing the Skill
[Tool usage]

### Step 4: Edit the Skill
[Content creation]

### Step 5: Packaging a Skill
[Distribution]

### Step 6: Iterate
[Improvement cycle]
```

**Key Techniques:**
- Process-oriented (Step 1, Step 2...)
- Multiple concrete examples per step
- References bundled scripts
- Uses imperative form throughout
- Comprehensive but organized

### Example 2: mcp-builder (Anthropic Official)

**Stats:**
- Size: 13,552 bytes
- Bundled references: 3 (best practices, Python guide, Node guide)
- Code examples: 15
- Workflow phases: 4
- Complete examples: 6

**Structure:**
```markdown
# MCP Server Development Guide

## Overview

## Process

### 🚀 High-Level Workflow

#### Phase 1: Deep Research and Planning
##### 1.1 Understand Agent-Centric Design Principles
##### 1.2 Study MCP Protocol Documentation
##### 1.3 Study Framework Documentation
##### 1.4 Exhaustively Study API Documentation
##### 1.5 Create Comprehensive Implementation Plan

#### Phase 2: Implementation
[Details...]

#### Phase 3: Testing & Validation
[Details...]

#### Phase 4: Documentation & Publishing
[Details...]
```

**Key Techniques:**
- Multi-level phase structure
- WebFetch instructions for loading external docs
- Progressive reference loading
- Agent-centric design principles
- Evaluation-driven development

### Example 3: pdf (Anthropic Document Skill)

**Stats:**
- Size: ~15,000 bytes
- Bundled assets: PDF manipulation libraries
- Code examples: 20+
- Sections: 12
- Frameworks covered: 3 (pypdf, pdfplumber, reportlab)

**Structure:**
```markdown
# PDF Processing Guide

## Overview

## Quick Start

## Python Libraries

### pypdf - Basic Operations
#### Merge PDFs
#### Split PDF
#### Extract Metadata
#### Rotate Pages

### pdfplumber - Text and Table Extraction
#### Extract Text with Layout
#### Extract Tables

### reportlab - PDF Creation
#### Create Simple PDF
#### Add Images
#### Create Tables

## Command-Line Tools

## Common Tasks

## Best Practices

## Troubleshooting
```

**Key Techniques:**
- Quick start section upfront
- Framework-specific organization
- Extensive code examples
- Common tasks highlighted
- Progressive complexity

---

## Enhancement Recommendations

### For Existing Simple Skills (Current State)

**Typical current state:**
- Size: 1,500-2,500 bytes
- Code examples: 2-3
- Workflow: 2-3 high-level steps
- No bundled resources

**Enhancement priorities:**

1. **Expand SKILL.md content (HIGH)**
   - Target 8,000+ bytes
   - Add 4-6 detailed workflow phases
   - Include 10-15 code examples
   - Add 3-5 complete scenarios

2. **Add bundled scripts (MEDIUM)**
   - Identify repetitive operations
   - Create automation utilities
   - Add validation scripts
   - Include setup helpers

3. **Add references (MEDIUM)**
   - Extract detailed content from SKILL.md
   - Create API documentation
   - Add schema definitions
   - Include best practices guides

4. **Add assets (LOW)**
   - Create configuration templates
   - Add example files
   - Include boilerplate code

5. **Fix writing style (HIGH)**
   - Convert to imperative form
   - Remove second person
   - Add clear action directives

### Quality Score Matrix

**Calculate score (0-100):**

- **Content depth (30 points):**
  - <2k bytes: 5 points
  - 2k-4k bytes: 10 points
  - 4k-6k bytes: 15 points
  - 6k-8k bytes: 22 points
  - 8k+ bytes: 30 points

- **Bundled resources (25 points):**
  - None: 0 points
  - 1 type (scripts OR references OR assets): 10 points
  - 2 types: 18 points
  - All 3 types: 25 points

- **Code examples (20 points):**
  - 0-2: 5 points
  - 3-5: 10 points
  - 6-9: 15 points
  - 10+: 20 points

- **Writing style (15 points):**
  - Mixed style: 5 points
  - Mostly imperative: 10 points
  - Fully imperative: 15 points

- **Progressive disclosure (10 points):**
  - No references to bundled resources: 0 points
  - Some references: 5 points
  - Systematic progressive disclosure: 10 points

**Grading:**
- 0-40: Needs significant enhancement
- 41-60: Good, could be better
- 61-80: Very good, minor improvements
- 81-100: Excellent, matches Anthropic quality

---

## Implementation Automation

### Gemini Prompt Template

```
You are enhancing a Claude Code plugin to match Anthropic's Agent Skills standards.

ANTHROPIC STANDARDS:
[Include this entire document]

CURRENT PLUGIN:
Name: {plugin_name}
Category: {category}
Current SKILL.md size: {size} bytes
Current quality score: {score}/100

Structure analysis:
{structure_json}

README excerpt:
{readme_excerpt}

TASK:
Analyze gaps and generate comprehensive SKILL.md following ALL Anthropic standards:

1. Proper frontmatter (hyphen-case name, multi-line description with triggers)
2. 8,000+ bytes content
3. Imperative/infinitive writing style (NO "you")
4. 4-6 detailed workflow phases
5. 10-15 code examples
6. 3-5 complete usage scenarios
7. References to bundled resources
8. Progressive disclosure pattern

OUTPUT: Complete SKILL.md file content (no explanations, just the file)
```

### Validation Checklist (Automated)

```python
def validate_skill(skill_md_path):
    with open(skill_md_path, 'r') as f:
        content = f.read()

    checks = {
        'has_frontmatter': content.startswith('---'),
        'size_adequate': len(content) >= 8000,
        'has_code_examples': content.count('```') >= 10,
        'uses_imperative': 'you should' not in content.lower(),
        'has_phases': 'Phase' in content or 'Step' in content,
        'references_resources': any([
            'scripts/' in content,
            'references/' in content,
            'assets/' in content
        ])
    }

    score = sum(checks.values()) / len(checks) * 100
    return score, checks
```

---

## Conclusion

This reference guide compiles all official Anthropic Agent Skills documentation and best practices. Use it as the authoritative source for:

1. **Manual skill creation** - Follow the process step-by-step
2. **Skill enhancement** - Compare existing skills against standards
3. **Automated enhancement** - Use as context for AI-powered upgrades
4. **Quality validation** - Check skills against the checklist

**Key Takeaways:**
- Skills = SKILL.md + optional bundled resources
- Target 8,000+ bytes with rich examples
- Use imperative form, avoid second person
- Implement progressive disclosure
- Reference scripts, references, and assets
- Follow the 6-step creation process

**For Automation:**
This document provides complete specifications for building automated enhancement systems that can analyze existing plugins and upgrade them to match Anthropic's quality standards.

---

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Source:** github.com/anthropics/skills (Official Repository)
