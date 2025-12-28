# Global Master Standard – Claude Skills Specification

**Document ID**: 6767-b-SPEC-DR-STND-claude-skills-standard.md
**Version**: 2.0.0
**Status**: AUTHORITATIVE - Single Source of Truth
**Created**: 2025-12-06
**Updated**: 2025-12-07

**Sources**:
- [Official Anthropic Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Official Anthropic Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Anthropic Engineering Blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Lee Han Chung Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)

---

## Executive Summary

### What Is a Claude Skill?

A Claude Skill is a **filesystem-based capability package** containing instructions, executable code, and resources that Claude can discover and use automatically. Skills are prompt-based context modifiers—NOT executable plugins or slash commands.

**Mental Model**: "Building a skill for an agent is like putting together an onboarding guide for a new hire."

### Why Use Skills Instead of Ad-Hoc Prompts?

| Aspect | Ad-Hoc Prompts | Skills |
|--------|---------------|--------|
| Reusability | One conversation | Persistent across all conversations |
| Discovery | Manual context provision | Automatic activation based on intent |
| Organization | Scattered knowledge | Structured packages |
| Context Management | Full context loaded | Progressive disclosure (on-demand) |
| Code Integration | Generated each time | Pre-written, deterministic scripts |

### Where Skills Live

| Location | Scope | Priority |
|----------|-------|----------|
| `~/.claude/skills/` | Personal (all projects) | 1 (lowest) |
| `.claude/skills/` | Project-specific | 2 |
| Plugin `skills/` directory | Plugin-bundled | 3 |
| Built-in skills | Platform-provided | 4 (highest) |

Later sources override earlier ones when names conflict.

---

## 1. Core Concepts

### Skill = What + When + How + Allowed Tools + Optional Model Override

Every skill answers:
- **What**: What capability does this provide?
- **When**: When should Claude activate it?
- **How**: Step-by-step instructions for Claude
- **Allowed Tools**: Which tools are pre-approved during execution?
- **Model Override**: Should a different model handle this? (optional)

### The Skill Tool Architecture

**Critical insight**: Skills are NOT in the system prompt.

Skills live in a meta-tool called `Skill` within the `tools` array:

```javascript
tools: [
  { name: "Read", ... },
  { name: "Write", ... },
  {
    name: "Skill",                    // Meta-tool (capital S)
    inputSchema: { command: string },
    description: "<available_skills>..." // Dynamic list of all skill descriptions
  }
]
```

### How Skills Are Discovered and Invoked

**Model-Invoked (Automatic)**:
1. At startup, Claude's system prompt includes metadata (name + description) for all skills
2. Claude reads user request and matches intent to skill descriptions
3. Claude invokes `Skill` tool with matching `command` parameter
4. No algorithmic routing, embeddings, or keyword matching—**pure LLM reasoning**

**User-Invoked (Manual)**:
- Type `/skill-name` to explicitly invoke a skill
- Required when `disable-model-invocation: true`

---

## 2. Folder & Discovery Layout

### Standard Directory Structure

```
skill-name/
├── SKILL.md              # REQUIRED - Instructions + YAML frontmatter
├── scripts/              # OPTIONAL - Executable Python/Bash scripts
│   ├── analyze.py
│   └── validate.py
├── references/           # OPTIONAL - Docs loaded into context
│   ├── API_REFERENCE.md
│   └── EXAMPLES.md
├── assets/               # OPTIONAL - Templates referenced by path
│   └── report_template.md
└── LICENSE.txt           # OPTIONAL - License terms
```

### Naming Conventions

**Best Practice**: Folder names SHOULD match the `name` field for clarity and maintainability.

> **Note**: Anthropic's official spec does NOT enforce folder/name matching at runtime. Claude Code will load skills regardless of folder name. However, matching names is strongly recommended for discoverability and team collaboration.

**Recommended**: Use **gerund form** (verb + -ing) for clarity:
- `processing-pdfs`
- `analyzing-spreadsheets`
- `generating-commit-messages`

**Acceptable alternatives**:
- Noun phrases: `pdf-processing`, `data-analysis`
- Action-oriented: `process-pdfs`, `analyze-data`

**Avoid**:
- Vague names: `helper`, `utils`, `tools`
- Generic names: `documents`, `data`, `files`
- Reserved words: `anthropic-*`, `claude-*`

### Directory Purposes

| Directory | Purpose | Loaded Into Context? | Token Cost |
|-----------|---------|---------------------|------------|
| `scripts/` | Executable code (deterministic operations) | No (executed via Bash) | None |
| `references/` | Documentation (API docs, examples) | Yes (via Read tool) | High |
| `assets/` | Templates, configs, static files | No (path reference only) | None |

**Key Insight**: Scripts execute without loading code into context. Only script OUTPUT consumes tokens.

---

## 3. SKILL.md Specification

### Complete Structure

```yaml
---
name: skill-name
description: What this skill does. Use when [conditions]. Trigger with "[phrases]".
---

# Skill Name

Brief purpose statement (1-2 sentences).

## Overview

What this skill does, when to use it, key capabilities.

## Prerequisites

Required tools, APIs, environment variables, packages.

## Instructions

### Step 1: [Action Verb]
[Imperative instructions]

### Step 2: [Action Verb]
[More instructions]

## Output

What artifacts this skill produces.

## Error Handling

Common failures and solutions.

## Examples

Concrete usage examples with input/output.

## Resources

Links to bundled files using {baseDir} variable.
```

---

## 4. YAML Frontmatter Fields

### Required Fields

#### `name`

**Type**: string
**Required**: YES
**Max Length**: 64 characters
**Constraints**:
- Lowercase letters, numbers, and hyphens only
- No XML tags
- Cannot contain reserved words: `"anthropic"`, `"claude"`

**Purpose**: Serves as the command identifier when Claude invokes the Skill tool.

**Examples**:
```yaml
name: processing-pdfs          # Good - gerund form
name: pdf-processing           # Good - noun phrase
name: PDF_Processing           # Bad - uppercase
name: claude-helper            # Bad - reserved word
```

#### `description`

**Type**: string
**Required**: YES
**Max Length**: 1024 characters
**Constraints**:
- Must be non-empty
- No XML tags
- Must use **third person** voice (injected into system prompt)

**Purpose**: Primary signal for Claude's skill selection. Claude uses this to decide when to activate the skill.

**Formula**:
```
[Primary capabilities]. [Secondary features]. Use when [scenarios]. Trigger with "[phrases]".
```

**Good Examples**:
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.

description: Generate descriptive commit messages by analyzing git diffs. Use when the user asks for help writing commit messages or reviewing staged changes.

description: Analyze Polymarket prediction market contracts using TimeGPT forecasting. Fetches contract odds, transforms to time series, generates price predictions with confidence intervals. Use when analyzing prediction markets, forecasting contract prices, or comparing platform odds. Trigger with 'forecast Polymarket', 'analyze prediction market'.
```

**Bad Examples**:
```yaml
description: Helps with documents          # Too vague
description: I can process your PDFs       # Wrong voice (first person)
description: You can use this for data     # Wrong voice (second person)
```

### Optional Fields

#### `allowed-tools`

**Type**: CSV string
**Required**: No
**Default**: No pre-approved tools (user prompted for each)

**Purpose**: Pre-approves tools **scoped to skill execution only**. Tools revert to normal permissions after skill completes.

**Syntax Examples**:
```yaml
# Multiple tools (comma-separated)
allowed-tools: "Read,Write,Glob,Grep,Edit"

# Scoped bash commands (restrict to specific commands)
allowed-tools: "Bash(git status:*),Bash(git diff:*),Read,Grep"

# NPM-scoped operations
allowed-tools: "Bash(npm:*),Bash(npx:*),Read,Write"

# Read-only audit
allowed-tools: "Read,Glob,Grep"
```

**Security Principle**: Grant ONLY tools the skill actually requires. Over-specifying creates unnecessary attack surface.

**NOTE**: Only supported in Claude Code, not claude.ai web version.

#### `model`

**Type**: string
**Required**: No
**Default**: `"inherit"` (use session model)

**Purpose**: Override the session model for skill execution.

**Examples**:
```yaml
model: inherit                           # Use current session model (default)
model: "claude-opus-4-20250514"          # Force specific model
model: "claude-sonnet-4-20250514"        # Use Sonnet
```

**Guidance**: Reserve model overrides for genuinely complex tasks. Higher-capability models increase cost and latency.

#### `version`

**Type**: string (semver)
**Required**: No
**Purpose**: Version tracking for skill evolution.

**Examples**:
```yaml
version: "1.0.0"    # Initial release
version: "1.1.0"    # New features
version: "2.0.0"    # Breaking changes
```

#### `license`

**Type**: string
**Required**: No
**Purpose**: License terms reference.

**Examples**:
```yaml
license: "MIT"
license: "Proprietary - See LICENSE.txt"
license: "Apache-2.0"
```

#### `mode`

**Type**: boolean
**Required**: No
**Default**: `false`

**Purpose**: When `true`, categorizes the skill as a "mode command" appearing in a prominent UI section separate from utility skills.

**Use Case**: Skills that fundamentally transform Claude's behavior for an extended session.

```yaml
mode: true     # Appears in "Mode Commands" section
mode: false    # Appears in regular skills list (default)
```

#### `disable-model-invocation`

**Type**: boolean
**Required**: No
**Default**: `false`

**Purpose**: When `true`, removes the skill from the `<available_skills>` list. Users can still invoke manually via `/skill-name`.

**Use Cases**:
- Dangerous operations requiring explicit user action
- Infrastructure/deployment skills
- Skills that should never auto-activate

```yaml
disable-model-invocation: true    # Manual invocation only
disable-model-invocation: false   # Auto-discovery enabled (default)
```

### Undocumented/Experimental Fields

#### `when_to_use`

**Status**: UNDOCUMENTED - Avoid in production

**Behavior**: Appends to `description` with hyphen separator.

**Recommendation**: Do NOT use. Rely on detailed `description` field instead. This field may change or be removed without notice.

---

## 4.5 Enterprise Extension Fields (Intent Solutions Standard)

These fields are NOT part of Anthropic's official spec but are required for skills published to the Claude Code Plugins marketplace (jeremylongshore/claude-code-plugins).

#### `author`

**Type**: string
**Required**: YES (for marketplace submission)
**Format**: `Name <email>` or `Name`

**Purpose**: Attribution for skill creator. Required for proper credit and contact.

**Examples**:
```yaml
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
author: "Jane Smith"
author: "Intent Solutions Team"
```

#### `tags`

**Type**: array of strings
**Required**: NO (recommended for discoverability)

**Purpose**: Categorization keywords for marketplace filtering.

**Examples**:
```yaml
tags:
  - devops
  - kubernetes
  - deployment

tags: ["security", "audit", "compliance"]
```

#### Enterprise Required Fields Summary

For marketplace submission, skills MUST include:

| Field | Anthropic Spec | Enterprise Required |
|-------|---------------|---------------------|
| `name` | Required | Required |
| `description` | Required | Required |
| `allowed-tools` | Optional | **Required** |
| `version` | Optional | **Required** |
| `author` | Not in spec | **Required** |
| `license` | Optional | **Required** |
| `tags` | Not in spec | Recommended |

---

## 5. Instruction-Body Best Practices

### Recommended Markdown Layout

```markdown
# [Skill Name]

[1-2 sentence purpose statement]

## Overview

[What this skill does, when to use it, key capabilities - 3-5 sentences]

## Prerequisites

**Required**:
- [Tool/API/package 1]
- [Tool/API/package 2]

**Environment Variables**:
- `API_KEY_NAME`: [Description]

**Optional**:
- [Nice-to-have dependency]

## Instructions

### Step 1: [Action Verb]

[Clear, imperative instructions]

### Step 2: [Action Verb]

[More instructions]

## Output

This skill produces:
- [File/artifact 1]
- [File/artifact 2]

## Error Handling

**Common Failures**:

1. **Error**: [Error message or condition]
   **Solution**: [How to fix]

2. **Error**: [Another failure]
   **Solution**: [Resolution]

## Examples

### Example 1: [Scenario]

**Input**:
[Example input]

**Output**:
[Example output]

### Example 2: [Advanced Scenario]

[Another example]

## Resources

- Advanced patterns: `{baseDir}/references/ADVANCED.md`
- API reference: `{baseDir}/references/API_DOCS.md`
- Utility script: `{baseDir}/scripts/validate.py`
```

### Content Guidelines

| Guideline | Requirement |
|-----------|-------------|
| **Size Limit** | Keep SKILL.md body under **500 lines** |
| **Token Budget** | Target ~2,500 tokens, max 5,000 tokens |
| **Language** | Use **imperative voice** ("Analyze data", not "You should analyze") |
| **Paths** | Always use `{baseDir}` variable, NEVER hardcode absolute paths |
| **Examples** | Include at least **2-3 concrete examples** with input/output |
| **Error Handling** | Document **4+ common failures** with solutions |
| **Voice** | Third person in descriptions, imperative in instructions |

### Progressive Disclosure Patterns

**When SKILL.md exceeds 400 lines, split content:**

**Pattern 1: High-level guide with references**
```markdown
# PDF Processing

## Quick start
[Basic instructions]

## Advanced features
**Form filling**: See [FORMS.md](FORMS.md)
**API reference**: See [REFERENCE.md](REFERENCE.md)
```

**Pattern 2: Domain-specific organization**
```
bigquery-skill/
├── SKILL.md (overview)
└── reference/
    ├── finance.md
    ├── sales.md
    └── product.md
```

**Pattern 3: Conditional details**
```markdown
For basic edits, modify XML directly.
**For tracked changes**: See [REDLINING.md](REDLINING.md)
```

### Critical Rule: One-Level-Deep References

**AVOID deeply nested references**. Claude may only partially read nested files.

**Bad**:
```
SKILL.md → advanced.md → details.md → actual_info.md
```

**Good**:
```
SKILL.md → advanced.md
SKILL.md → reference.md
SKILL.md → examples.md
```

---

## 6. Security & Safety Guidance

### Choosing `allowed-tools` Conservatively

**Principle of Least Privilege**: Grant ONLY tools the skill actually needs.

**Good Examples**:
```yaml
# Read-only audit skill
allowed-tools: "Read,Glob,Grep"

# File transformation skill
allowed-tools: "Read,Write,Edit"

# Git operations only
allowed-tools: "Bash(git:*),Read,Grep"
```

**Bad Examples**:
```yaml
# Overly permissive - unnecessary attack surface
allowed-tools: "Bash,Read,Write,Edit,Glob,Grep,WebSearch,Task,Agent"

# Unscoped bash - allows any command
allowed-tools: "Bash"
```

### When to Use `disable-model-invocation: true`

Set this flag for skills that:
- Perform destructive operations (delete files, drop databases)
- Deploy to production environments
- Access sensitive credentials
- Run irreversible commands
- Should NEVER auto-activate

```yaml
---
name: deploy-production
description: Deploy application to production. Dangerous - requires explicit invocation.
disable-model-invocation: true
allowed-tools: "Bash(deploy:*),Read,Glob"
---
```

### Security Considerations

**CRITICAL**: Only use Skills from trusted sources.

Before using an untrusted skill:
- [ ] Review all bundled files (SKILL.md, scripts, resources)
- [ ] Check for unusual network calls
- [ ] Inspect scripts for malicious code
- [ ] Verify tool invocations match stated purpose
- [ ] Validate external URLs (if any)

**Malicious skills could**:
- Exfiltrate data via network calls
- Access unauthorized files
- Misuse tools (Bash for system manipulation)
- Inject instructions overriding safety guidelines

---

## 7. Model Selection Guidance

### When to Inherit vs Override

| Scenario | Recommendation |
|----------|----------------|
| Most skills | `model: inherit` or omit field |
| Complex reasoning required | Consider `claude-opus-4-*` |
| Fast, simple tasks | `claude-haiku-*` |
| Balanced performance | `claude-sonnet-4-*` |

### Trade-offs

| Model | Speed | Cost | Capability |
|-------|-------|------|------------|
| Haiku | Fast | Low | Basic tasks |
| Sonnet | Balanced | Medium | Most tasks |
| Opus | Slower | High | Complex reasoning |

### Testing Across Models

**Always test skills with all models you plan to use:**

- **Haiku**: Does the skill provide sufficient guidance?
- **Sonnet**: Is content clear and efficient?
- **Opus**: Are instructions avoiding over-explanation?

What works for Opus may need more detail for Haiku.

---

## 8. Production-Readiness Checklist

### Naming & Description

- [ ] `name` matches folder name (lowercase + hyphens)
- [ ] `name` is under 64 characters
- [ ] `description` under 1024 characters
- [ ] `description` uses third person voice
- [ ] `description` includes what + when + trigger phrases
- [ ] No reserved words (`anthropic`, `claude`)

### Structure & Tools

- [ ] SKILL.md at root of skill folder
- [ ] Body under 500 lines
- [ ] Uses `{baseDir}` for all paths
- [ ] No hardcoded absolute paths
- [ ] `allowed-tools` includes only necessary tools
- [ ] Forward slashes in all paths (not backslashes)

### Instructions Quality

- [ ] Has all required sections (Overview, Prerequisites, Instructions, Output, Error Handling, Examples, Resources)
- [ ] Uses imperative voice
- [ ] 2-3 concrete examples with input/output
- [ ] 4+ common errors documented with solutions
- [ ] One-level-deep file references only

### Testing

- [ ] Tested with Haiku, Sonnet, and Opus
- [ ] Trigger phrases activate skill correctly
- [ ] Scripts execute without errors
- [ ] Examples produce expected output
- [ ] No false positive activations

---

## 9. Versioning & Evolution

### Semantic Versioning

```
MAJOR.MINOR.PATCH
  │     │     └── Bug fixes, clarifications
  │     └──────── New features, additive changes
  └────────────── Breaking changes to interface
```

**Examples**:
- `1.0.0` → Initial release
- `1.1.0` → Added new workflow step
- `1.0.1` → Fixed typo in instructions
- `2.0.0` → Changed output format (breaking)

### Changelog Notes

Include version history in SKILL.md:

```markdown
## Version History

- **v2.0.0** (2025-12-01): Breaking - Changed output format to JSON
- **v1.1.0** (2025-11-15): Added batch processing support
- **v1.0.0** (2025-11-01): Initial release
```

### Deprecation Strategy

When deprecating a skill:

1. Add deprecation notice to description:
   ```yaml
   description: "[DEPRECATED - Use new-skill instead] Original description..."
   ```

2. Set `disable-model-invocation: true` to prevent auto-activation

3. Keep skill available for manual invocation during transition

4. Remove entirely in next major version

---

## 10. Canonical SKILL.md Template

```yaml
---
name: your-skill-name
description: |
  [Primary capabilities as action verbs]. [Secondary features].
  Use when [3-4 trigger scenarios].
  Trigger with "[phrase 1]", "[phrase 2]", "[phrase 3]".
allowed-tools: "Read,Write,Glob,Grep,Edit"
version: "1.0.0"
---

# [Skill Name]

[1-2 sentence purpose statement explaining what this skill does.]

## Overview

[3-5 sentences covering:]
- What this skill does
- When to use it
- Key capabilities
- What it produces

## Prerequisites

**Required**:
- [Tool/API/package 1]: [Brief purpose]
- [Tool/API/package 2]: [Brief purpose]

**Environment Variables**:
- `ENV_VAR_NAME`: [Description and how to obtain]

**Optional**:
- [Nice-to-have dependency]: [When needed]

## Instructions

### Step 1: [Action Verb - e.g., "Analyze Input"]

[Clear, imperative instructions for this step]

```bash
# Example command if applicable
python {baseDir}/scripts/step1.py --input data.json
```

**Expected result**: [What should happen]

### Step 2: [Action Verb - e.g., "Transform Data"]

[Instructions for next step]

### Step 3: [Action Verb - e.g., "Generate Output"]

[Final step instructions]

## Output

This skill produces:

- **[Artifact 1]**: [Description and format]
- **[Artifact 2]**: [Description and format]
- **[Report/Summary]**: [Description]

## Error Handling

### Common Failures

1. **Error**: `[Error message or condition]`
   **Cause**: [Why this happens]
   **Solution**: [How to fix]

2. **Error**: `[Another error]`
   **Cause**: [Reason]
   **Solution**: [Resolution]

3. **Error**: `[Third error]`
   **Cause**: [Reason]
   **Solution**: [Fix]

4. **Error**: `[Fourth error]`
   **Cause**: [Reason]
   **Solution**: [Fix]

## Examples

### Example 1: [Basic Scenario]

**User Request**: "[What user says]"

**Input**:
```
[Example input data]
```

**Output**:
```
[Expected output]
```

### Example 2: [Advanced Scenario]

**User Request**: "[More complex request]"

**Input**:
```
[Input data]
```

**Output**:
```
[Expected result]
```

## Resources

**Reference Documentation**:
- API reference: `{baseDir}/references/API_REFERENCE.md`
- Advanced patterns: `{baseDir}/references/ADVANCED.md`

**Utility Scripts**:
- Data processor: `{baseDir}/scripts/process.py`
- Validator: `{baseDir}/scripts/validate.py`

**Templates**:
- Report template: `{baseDir}/assets/report_template.md`

## Version History

- **v1.0.0** (YYYY-MM-DD): Initial release
```

---

## 11. Minimal Example Skill

### Structured PR Review Helper

```yaml
---
name: reviewing-pull-requests
description: |
  Analyze pull request diffs and generate structured code reviews.
  Checks for bugs, security issues, performance problems, and style violations.
  Use when reviewing PRs, analyzing code changes, or checking diffs.
  Trigger with "review this PR", "check my code changes", "analyze diff".
allowed-tools: "Read,Grep,Glob,Bash(git:*)"
version: "1.0.0"
---

# Structured PR Review Helper

Generate comprehensive, structured code reviews from git diffs.

## Overview

This skill analyzes code changes and produces structured review feedback covering:
- Bug detection and edge cases
- Security vulnerabilities
- Performance considerations
- Code style and maintainability
- Test coverage gaps

## Prerequisites

**Required**:
- Git repository with staged or committed changes
- Read access to codebase

**Optional**:
- Project-specific style guide in `.github/STYLE_GUIDE.md`

## Instructions

### Step 1: Get the Diff

```bash
# For staged changes
git diff --staged

# For specific PR/branch
git diff main...feature-branch
```

### Step 2: Analyze Each Changed File

For each modified file:
1. Read the full file for context
2. Identify the nature of changes (new feature, bug fix, refactor)
3. Check for issues in each category

### Step 3: Generate Structured Review

Produce review in this format:

```markdown
## PR Review: [Brief Title]

### Summary
[1-2 sentence overview of changes]

### Findings

#### Critical Issues
- [ ] [Issue description with file:line reference]

#### Suggestions
- [ ] [Improvement suggestion]

#### Questions
- [ ] [Clarification needed]

### Recommendation
[APPROVE / REQUEST_CHANGES / COMMENT]
```

## Output

- Structured markdown review
- Categorized findings (Critical, Suggestions, Questions)
- Clear recommendation

## Error Handling

1. **Error**: No diff available
   **Solution**: Ensure changes are staged or specify correct branch comparison

2. **Error**: Binary files in diff
   **Solution**: Skip binary files, note in review that manual check needed

3. **Error**: Large diff (>1000 lines)
   **Solution**: Focus on most critical files, suggest splitting PR

4. **Error**: Missing context (file deleted)
   **Solution**: Note inability to review deleted code, focus on remaining changes

## Examples

### Example 1: Simple Bug Fix Review

**User Request**: "Review my bug fix PR"

**Output**:
```markdown
## PR Review: Fix null pointer in user validation

### Summary
Adds null check before accessing user.email property.

### Findings

#### Critical Issues
- None

#### Suggestions
- [ ] Consider adding unit test for null user case (src/validation.ts:45)

#### Questions
- [ ] Should we also check for empty string?

### Recommendation
APPROVE - Good defensive fix, minor test suggestion
```

### Example 2: Security-Sensitive Change

**User Request**: "Check this authentication change"

**Output**:
```markdown
## PR Review: Update JWT token validation

### Summary
Modifies token expiration handling and adds refresh token support.

### Findings

#### Critical Issues
- [ ] Token secret exposed in error message (src/auth.ts:78)
- [ ] Missing rate limiting on refresh endpoint (src/routes/auth.ts:112)

#### Suggestions
- [ ] Add token rotation on refresh
- [ ] Log authentication failures for monitoring

### Recommendation
REQUEST_CHANGES - Security issues must be addressed
```
```

---

## 12. Author Checklist

Run through this checklist every time you create or update a skill:

### Before Writing

- [ ] Identified clear, single-purpose capability
- [ ] Confirmed no existing skill handles this
- [ ] Gathered all necessary reference materials

### Frontmatter (Anthropic Spec)

- [ ] `name`: lowercase, hyphens, under 64 chars
- [ ] `description`: third person, under 1024 chars, includes what + when + triggers
- [ ] `allowed-tools`: minimal necessary tools only (optional per spec)
- [ ] `version`: semver format (optional per spec)

### Enterprise Fields (Marketplace Submission)

- [ ] `allowed-tools`: Required - list only necessary tools
- [ ] `version`: Required - semver format (e.g., 1.0.0)
- [ ] `author`: Required - format: `Name <email>`
- [ ] `license`: Required - MIT recommended
- [ ] `tags`: Recommended - array of category keywords

### Content

- [ ] Body under 500 lines
- [ ] All required sections present
- [ ] Imperative voice throughout instructions
- [ ] `{baseDir}` used for all paths
- [ ] 2-3 concrete examples with input/output
- [ ] 4+ errors documented with solutions
- [ ] One-level-deep references only

### Testing

- [ ] Triggers correctly on intended phrases
- [ ] Does NOT trigger on unrelated requests
- [ ] Scripts execute successfully
- [ ] Tested with multiple models (Haiku, Sonnet, Opus)
- [ ] Team review completed (if applicable)

### Security

- [ ] No secrets or credentials in skill
- [ ] Tools appropriately scoped
- [ ] Dangerous operations require explicit invocation
- [ ] External dependencies audited

---

## 13. Open Questions / Potentially Out-of-Date Areas

### Confirmed Speculative or Unclear

1. **`when_to_use` field**: Exists in codebase but undocumented. Behavior may change. Recommendation: avoid in production.

2. **Token budget limits**: The 15,000-character limit for skill descriptions is from Lee Han Chung's analysis, not official docs. May vary by platform.

3. **Model override behavior**: Exact list of supported model IDs not documented. Test with specific models before relying on overrides.

4. **Concurrency**: Skills are described as "not concurrency-safe" but exact failure modes unclear. Avoid simultaneous skill invocations.

5. **`allowed-tools` on claude.ai**: Official docs state this field is only supported in Claude Code, not the web version.

### How to Verify

1. **Test skill behavior directly** in Claude Code with various model settings
2. **Monitor Anthropic's official changelog** for updates to Skills API
3. **Check Claude Code release notes** for new frontmatter fields
4. **Review official GitHub repo** at https://github.com/anthropics/skills for reference implementations

### Areas Requiring Human Review

- Platform-specific behavior differences (API vs claude.ai vs Claude Code)
- New frontmatter fields added in future releases
- Changes to token budgets or context limits
- Model-specific guidance as new models release

---

## References

### Official Anthropic Documentation

- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Anthropic Engineering Blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Official Skills Repository](https://github.com/anthropics/skills)

### Community Resources

- [Lee Han Chung Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Simon Willison on Claude Skills](https://simonwillison.net/2025/Oct/16/claude-skills/)

---

**Last Updated**: 2025-12-07
**Maintained By**: Intent Solutions (Jeremy Longshore)
**Status**: AUTHORITATIVE - Single Source of Truth for Claude Skills Development
