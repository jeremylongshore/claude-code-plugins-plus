# Global Master Standard – Claude Skills Specification

**Document ID**: 077-SPEC-MASTER-claude-skills-standard.md
**Version**: 2.3.0
**Status**: AUTHORITATIVE - Single Source of Truth
**Created**: 2025-12-06
**Updated**: 2025-12-08
**Audited Against**:
- Anthropic Engineering Blog (ENGINEERING SOURCE - oldest, deepest technical insights)
- Official Anthropic Skills Blog (PRIMARY SOURCE - newest product guidance)
- Lee Han Chung Deep Dive (implementation details)

**Sources**:
- [Official Anthropic Skills Blog Post](https://claude.com/blog/skills) ⭐ **PRIMARY SOURCE**
- [Anthropic Engineering Blog - Skills Deep Dive](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) ⭐ **ENGINEERING SOURCE**
- [Official Anthropic Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Official Anthropic Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Lee Han Chung Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)

---

## Executive Summary

### What Is a Claude Skill?

A Claude Skill is a **filesystem-based capability package** containing instructions, executable code, and resources that Claude can discover and use automatically. Skills are prompt-based context modifiers—NOT executable plugins or slash commands.

**Official Definition** (Anthropic): "Specialized capability packages that extend Claude's functionality for specific tasks. Claude will only access a skill when it's relevant to the task at hand."

**Mental Model**: "Building a skill for an agent is like putting together an onboarding guide for a new hire."

### Four Core Design Principles (Anthropic Official)

Skills are architecturally designed with four foundational attributes:

1. **Composable**
   - Multiple skills work together seamlessly
   - Claude automatically identifies and coordinates which skills are needed
   - No manual orchestration required
   - **Nixtla Impact**: `nixtla-schema-mapper` + `nixtla-experiment-architect` can chain automatically

2. **Portable**
   - Same skill format works across ALL platforms:
     - Claude apps (claude.ai web/mobile)
     - Claude Code (CLI tool)
     - Claude API (Messages API)
   - Write once, deploy everywhere
   - **Nixtla Impact**: Internal skills work for web users, API customers, and CLI developers

3. **Efficient**
   - Loads only minimal necessary information when needed
   - Progressive disclosure pattern (description → full instructions → resources)
   - Avoids context window bloat
   - **Nixtla Impact**: 40+ skill portfolio won't overwhelm context if designed properly

4. **Powerful**
   - Can include executable code for reliable task performance
   - Pre-written scripts eliminate non-determinism
   - Combines prompts + execution for complete workflows
   - **Nixtla Impact**: TimeGPT API calls, pandas transformations, validation scripts all executable

**Code Execution Performance Economics** (Anthropic Engineering):

> **"Sorting a list via token generation is far more expensive than simply running a sorting algorithm."**

Deterministic code execution provides **orders of magnitude** cost/performance advantages:

| Operation | Token Generation | Code Execution | Advantage |
|-----------|------------------|----------------|-----------|
| **Sort 1000 items** | ~2,000 tokens (~$0.006) | <10 tokens for script call (~$0.00003) | **200x cheaper** |
| **Pandas transform** | ~5,000 tokens loading data + code | Script runs without context load | **No context cost** |
| **TimeGPT API call** | Non-deterministic, requires retry logic | Deterministic, runs once | **Reliable + cheap** |

**Nixtla Production Impact**:
- TimeGPT forecasting loops: Execute via script, not token generation
- Schema validation: Run validation.py, don't describe validation in tokens
- Data transformations: pandas scripts consume ZERO context tokens
- Experiment harnesses: Pre-written Python orchestration

**Production Implication for Nixtla**: These four principles guide ALL architectural decisions. Violating any principle (non-composable, platform-locked, context-heavy, prompt-only) indicates poor skill design.

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

### Message Injection Architecture

**CRITICAL FOR NIXTLA INTERNAL TEAMS**: Understanding how skills inject into conversations ensures predictable behavior in production workflows.

When a skill is invoked, it injects **two user messages** into the conversation:

#### Message 1: Metadata Message (Visible to User)
```javascript
{
  role: "user",
  isMeta: false,  // Visible in UI
  content: [
    {
      type: "text",
      text: "<command-message>skill-name is loading...</command-message>"
    }
  ]
}
```

**Purpose**: Provides transparent UI feedback that a skill is executing.

#### Message 2: Skill Prompt Message (Hidden from User)
```javascript
{
  role: "user",
  isMeta: true,   // Hidden from UI, sent to API only
  content: [
    {
      type: "text",
      text: "[Full SKILL.md content with {baseDir} substitutions]"
    }
  ]
}
```

**Purpose**: Injects skill instructions directly into Claude's context for reasoning.

#### XML Tag Structure

Skills use specific XML tags for message formatting:
- `<command-message>` - Wraps the visible status indicator
- `<command-name>` - Contains the skill name for tracking
- `<available_skills>` - Lists all discoverable skills in Skill tool description

**Production Impact for Nixtla**:
- Skills don't pollute conversation history visible to users
- Skill instructions consume context budget (tracked via `isMeta: true` messages)
- Multiple skill invocations in one session stack context linearly
- **Context budget management is critical** (see Section 4 for limits)

#### Chain-of-Thought Visibility (UX Insight)

**OFFICIAL ANTHROPIC**: "Users can view skills in Claude's chain-of-thought output while it works."

When Claude invokes skills, users see them in the reasoning trace/thinking blocks. This provides:
- **Transparency**: Users know which skills are active
- **Debuggability**: Developers can trace skill activation patterns
- **Trust**: Users understand Claude's decision-making process

**Nixtla Customer Impact**:
- TimeGPT customers will SEE when `nixtla-experiment-architect` activates
- Internal teams can debug skill selection by reviewing chain-of-thought
- Enterprise admins can audit which skills employees trigger

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

**Folder names must match the `name` field exactly.**

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
| `004-scripts/` | Executable code (deterministic operations) | No (executed via Bash) | None |
| `references/` | Documentation (API docs, examples) | Yes (via Read tool) | High |
| `assets/` | Templates, configs, static files | No (path reference only) | None |

**Key Insight**: Scripts execute without loading code into context. Only script OUTPUT consumes tokens.

---

### Platform-Specific Implementation & Distribution

#### Claude Apps (claude.ai, mobile)

**Availability**: Pro, Max, Team, and Enterprise users

**Installation Methods**:
1. **Official Skill-Creator Tool** (Anthropic Recommended)
   - Use the built-in `skill-creator` skill for interactive guidance
   - No manual file editing required
   - Provides step-by-step skill creation workflow
   - Available via slash command: `/skill-creator`

2. **Manual Installation**:
   - Create `.claude/skills/skill-name/SKILL.md` structure
   - Upload to project or personal workspace

**Admin Controls** (Team/Enterprise):
- Admins must **enable skills organization-wide** via Settings
- Organization-level toggle controls all member access
- **NIXTLA ENTERPRISE NOTE**: Customers need admin approval before deploying skills

**Official Pre-built Skills** (Anthropic-provided):
- Excel processing
- PowerPoint manipulation
- Word document editing
- Fillable PDF handling

**Nixtla Strategy**: Leverage pre-built skills where possible; avoid reinventing document processing.

---

#### Claude API (Messages API)

**⚠️ CRITICAL FOR NIXTLA API INTEGRATIONS**:

**New `/v1/skills` Endpoint**:
- Programmatic skill control, versioning, and management
- Separate from Messages API calls
- Enables automated skill deployment and updates

**Code Execution Tool Requirement**:
- Skills with executable scripts **require Code Execution Tool beta**
- Must be enabled in API configuration
- Provides secure sandbox for script execution
- **BLOCKER**: Nixtla's TimeGPT/pandas/validation scripts won't work without this beta feature

**Implementation Pattern** (Nixtla API Integration):
```python
# 1. Enable Code Execution Tool beta in API settings
# 2. Deploy skills via /v1/skills endpoint
# 3. Reference skills in Messages API calls

import anthropic

client = anthropic.Anthropic(api_key="...")

# Deploy skill (one-time)
skill_response = client.skills.create(
    skill_content=skill_md_content,
    version="1.0.0"
)

# Use skill in conversation
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Map my data to Nixtla schema"}],
    # Skills automatically discovered and invoked
)
```

**Production Requirements for Nixtla**:
1. Request Code Execution Tool beta access from Anthropic
2. Implement `/v1/skills` deployment automation
3. Version all skills semantically (1.0.0, 1.1.0, etc.)
4. Test scripts in sandbox environment before production

---

#### Claude Code (CLI)

**Installation Methods**:
1. **Marketplace Plugins** (Anthropic Official):
   - Install via `anthropics/skills` marketplace
   - Managed updates and versioning
   - **NIXTLA DISTRIBUTION**: Consider publishing nixtla-skills as marketplace plugin

2. **Manual Installation**:
   - Place skills in `~/.claude/skills/` (personal, all projects)
   - Place skills in `.claude/skills/` (project-specific)
   - **Version control friendly**: Commit `.claude/skills/` to git repos

**Priority Hierarchy**:
```
~/.claude/skills/          Priority 1 (lowest)
.claude/skills/            Priority 2
Plugin skills/             Priority 3
Built-in skills            Priority 4 (highest)
```

Later sources override earlier ones when names conflict.

**Nixtla Distribution Strategy**:
- Primary: Project-specific (`.claude/skills/nixtla-*/`)
- Fallback: Personal installation (`~/.claude/skills/nixtla-*/`)
- Future: Marketplace plugin for external distribution

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
**Max Length**: 1024 characters per skill
**Constraints**:
- Must be non-empty
- No XML tags
- Must use **third person** voice (injected into system prompt)
- **CRITICAL BUDGET LIMIT**: All skill descriptions combined have a 15,000-character context budget

**Purpose**: Primary signal for Claude's skill selection. Claude uses this to decide when to activate the skill.

**⚠️ PRODUCTION CONSTRAINT FOR NIXTLA TEAMS**:

The Skill tool's description field has a **15,000-character token budget** across ALL skills in the workspace. If your combined skill descriptions exceed this limit, Claude will silently filter out skills, causing unpredictable skill discovery failures.

**Critical Formula**:
```
(Number of Skills) × (Avg Chars per Description) < 15,000 chars
```

**Best Practices for Scaling Skill Portfolios**:
- **Target 300-400 characters per skill** (not the 1024 maximum)
- **Monitor total character count** across all skill descriptions in workspace
- Verbose descriptions don't improve intent matching—specificity does
- If skills stop activating unexpectedly, audit total description length first

**Scaling Examples**:
```
10 skills × 400 chars = 4,000 chars   (✅ safe, 11,000 chars headroom)
20 skills × 400 chars = 8,000 chars   (✅ safe, 7,000 chars headroom)
30 skills × 400 chars = 12,000 chars  (⚠️ risky, approaching limit)
40 skills × 400 chars = 16,000 chars  (❌ exceeds budget, filtering likely)

20 skills × 750 chars = 15,000 chars  (⚠️ at limit exactly, no headroom)
30 skills × 500 chars = 15,000 chars  (⚠️ at limit exactly, no headroom)
```

**Production Monitoring for Nixtla**:
```bash
# Audit total description length across all skills
find .claude/skills/nixtla-*/SKILL.md -exec grep -A 5 '^description:' {} \; | wc -c
```

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
| **Word Count** | Target ~1,500-2,500 words, **max 5,000 words** to avoid context saturation |
| **Token Budget** | Target ~2,500 tokens, max 5,000 tokens |
| **Language** | Use **imperative voice** ("Analyze data", not "You should analyze") |
| **Paths** | Always use `{baseDir}` variable, NEVER hardcode absolute paths |
| **Examples** | Include at least **2-3 concrete examples** with input/output |
| **Error Handling** | Document **4+ common failures** with solutions |
| **Voice** | Third person in descriptions, imperative in instructions |

**⚠️ NIXTLA PRODUCTION GUIDANCE**: The 5,000-word limit prevents context window saturation. Symptoms of oversized SKILL.md files include:
- Skills randomly failing to complete workflows
- Partial instruction execution
- Claude "forgetting" later sections of skill instructions
- Increased token costs per skill invocation

**For production skill portfolios at scale**: Aim for 1,500-2,000 words per SKILL.md to leave headroom for:
- Multiple skill invocations in one session
- User conversation context
- Tool output accumulation
- Growing skill count over time

### Progressive Disclosure Patterns

**⚠️ CRITICAL ENGINEERING INSIGHT** (Anthropic Engineering Blog):

> **"The amount of context that can be bundled into a skill is effectively unbounded"**

**Three-Tier Disclosure Architecture**:
1. **Tier 1**: Metadata (name/description) - Pre-loaded in system prompt at startup (~100 chars)
2. **Tier 2**: Full SKILL.md - Loaded when skill activates (~2,000 tokens)
3. **Tier 3**: Referenced files - Loaded on-demand only when contextually necessary (0 tokens until needed)

**Production Implication for Nixtla**:

You can bundle MASSIVE reference materials without context penalty:
- Entire TimeGPT API documentation (10,000+ words)
- Complete model comparison tables
- Exhaustive troubleshooting guides
- Full example library

**Key**: Only Tier 1 (description) counts against the 15,000-char budget. Tier 2 and Tier 3 load dynamically, so total skill content can be "effectively unbounded."

**Example** (nixtla-timegpt-lab):
```
Tier 1: 400-char description (always loaded)
Tier 2: 2,000-word SKILL.md (loaded when activated)
Tier 3: references/
  ├── TIMEGPT_API_COMPLETE.md (15,000 words - loaded only if API questions)
  ├── TROUBLESHOOTING_GUIDE.md (8,000 words - loaded only if errors)
  └── EXAMPLES_LIBRARY.md (20,000 words - loaded only if user asks for examples)

Total potential: 43,000+ words, but context cost = 400 chars + dynamic loading
```

---

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

**Pattern 4: Mutually Exclusive Contexts** (Anthropic Engineering)

**Engineering Insight**:
> "This separation reduces token usage for mutually exclusive contexts."

When skill capabilities have contexts that are NEVER used together, split them into separate reference files. Only the contextually relevant file loads.

**Example** (PDF Skill from Anthropic):
```
pdf-skill/
├── SKILL.md (core capabilities)
├── reference.md (general PDF manipulation)
└── forms.md (form-filling workflows - ONLY loads if task involves forms)
```

If user asks "extract text from PDF", `forms.md` never loads (mutually exclusive context).

**Nixtla Production Pattern**:
```
nixtla-timegpt-lab/
├── SKILL.md (core orchestration)
├── references/
│   ├── TIMEGPT_FORECASTING.md (forecasting workflows)
│   ├── TIMEGPT_FINETUNING.md (fine-tuning workflows - mutually exclusive)
│   ├── TIMEGPT_ANOMALY_DETECTION.md (anomaly detection - mutually exclusive)
│   └── TIMEGPT_TROUBLESHOOTING.md (debugging - loaded only on errors)
```

**Key Insight**: If a user is fine-tuning, they're NOT doing anomaly detection. Don't waste context loading both.

**Decision Tree**:
```
Task: "Run TimeGPT forecast"
→ Loads: SKILL.md + TIMEGPT_FORECASTING.md
→ Skips: FINETUNING.md, ANOMALY_DETECTION.md, TROUBLESHOOTING.md

Task: "Fine-tune TimeGPT model"
→ Loads: SKILL.md + TIMEGPT_FINETUNING.md
→ Skips: FORECASTING.md, ANOMALY_DETECTION.md, TROUBLESHOOTING.md

Error encountered:
→ Additionally loads: TIMEGPT_TROUBLESHOOTING.md
```

**Context Savings**:
```
Without pattern: 43,000 words loaded (all reference files)
With pattern: 2,000 (SKILL.md) + 8,000 (relevant context) = 10,000 words
Savings: 76% context reduction
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

**⚠️ CRITICAL FOR NIXTLA PRODUCTION SKILLS**: Tool permissions are **scoped to skill execution only** and **automatically revert** when the skill completes. This temporary escalation pattern ensures:
- Skills can't permanently expand Claude's attack surface
- Tool permissions return to user-controlled defaults after execution
- Multiple skill invocations in one session maintain isolation

**Lifecycle Example**:
```
1. User session starts → Standard tool permissions active
2. nixtla-experiment-architect invokes → allowed-tools: "Read,Write,Bash(python:*),Grep,Glob"
3. Skill executes experiments → Pre-approved tools available without prompts
4. Skill completes → Permissions revert to standard session defaults
5. Next skill invocation → New temporary permission scope
```

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

### Frontmatter

- [ ] `name`: lowercase, hyphens, under 64 chars, matches folder
- [ ] `description`: third person, under 1024 chars, includes what + when + triggers
- [ ] `allowed-tools`: minimal necessary tools only
- [ ] `version`: semver format

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

## 14. Validation & Error Handling

### Five Skill Tool Validation Error Codes

When skills fail to invoke, Claude's Skill tool returns one of five error codes:

#### Error 1: Empty Command Input
**Symptom**: Skill tool called without `command` parameter
```javascript
{ error: "Empty command input" }
```
**Cause**: Missing or null `command` field in Skill tool invocation
**Fix**: Ensure Claude passes valid skill name (e.g., `command: "nixtla-schema-mapper"`)

#### Error 2: Unknown/Unavailable Skill
**Symptom**: Skill name not found in discovered skills list
```javascript
{ error: "Unknown skill: foo-bar" }
```
**Cause**:
- Skill not in `.claude/skills/` directory
- SKILL.md filename incorrect (must be `SKILL.md`, case-sensitive on some systems)
- Frontmatter `name` field doesn't match directory name
**Fix**: Verify skill installation, check directory/file naming

#### Error 3: Skill File Loading Failure
**Symptom**: SKILL.md exists but can't be parsed
```javascript
{ error: "Failed to load skill: invalid-yaml" }
```
**Cause**:
- Malformed YAML frontmatter (missing `---` delimiters, invalid syntax)
- File encoding issues (non-UTF-8 characters)
- Permission errors (file not readable)
**Fix**: Validate YAML syntax, check file permissions, ensure UTF-8 encoding

#### Error 4: Model Invocation Disabled
**Symptom**: Skill has `disable-model-invocation: true` but was auto-triggered
```javascript
{ error: "Model invocation disabled for skill: deploy-production" }
```
**Cause**: Claude attempted auto-activation on a manual-only skill
**Fix**: User must invoke manually via `/skill-name` slash command

#### Error 5: Non-Prompt-Based Skill Type
**Symptom**: Skill type not supported (experimental/future feature)
```javascript
{ error: "Skill type not supported: executable" }
```
**Cause**: Attempting to use experimental skill types beyond standard prompt-based skills
**Fix**: Use only standard prompt-based skills with SKILL.md structure

### Progressive Testing Workflow for Nixtla Skills

Follow this 5-step progression when validating new skills:

#### Step 1: Validate Frontmatter YAML Structure
```bash
# Test YAML parsing
python -c "import yaml; yaml.safe_load(open('.claude/skills/nixtla-*/SKILL.md').read().split('---')[1])"
```
**Validates**: Syntax correctness, required fields (`name`, `description`)

#### Step 2: Test Prompt Injection with Minimal Workflow
- Invoke skill manually: `/nixtla-skill-name`
- Check `<command-message>` appears in UI
- Verify skill instructions load without truncation
- Confirm skill completes without errors

**Validates**: Message injection, context loading, basic execution

#### Step 3: Verify Tool Permissions Enforcement
- Test that `allowed-tools` grants expected permissions
- Verify disallowed tools still require user approval
- Confirm permissions revert after skill completion

**Validates**: Security scoping, temporary escalation

#### Step 4: Execute Full Workflow with Bundled Resources
- Test `{baseDir}` path substitutions
- Execute bundled `scripts/` via Bash tool
- Load `references/` docs via Read tool
- Verify `assets/` templates accessible

**Validates**: Resource loading, script execution, path resolution

#### Step 5: Confirm Context Injection Behavior
- Monitor token usage during skill execution
- Test multiple skill invocations in one session
- Verify no context pollution between invocations
- Check skill doesn't interfere with other skills

**Validates**: Context isolation, budget management, multi-skill compatibility

---

## 15. Anti-Patterns & Common Mistakes

### Critical Anti-Patterns for Nixtla Production Skills

#### Anti-Pattern 1: Hardcoded Absolute Paths
❌ **BAD**:
```markdown
Run: `python /home/user/nixtla-skills/scripts/analyze.py`
See: `/Users/max/projects/nixtla/docs/API_REFERENCE.md`
```

✅ **GOOD**:
```markdown
Run: `python {baseDir}/scripts/analyze.py`
See: `{baseDir}/references/API_REFERENCE.md`
```

**Why this fails**: Breaks portability across different installations, team members, CI/CD environments.

---

#### Anti-Pattern 2: Embedding 10,000+ Word Reference Material
❌ **BAD**:
```markdown
## TimeGPT API Reference

[5,000 words of API documentation embedded in SKILL.md]
[Another 3,000 words of examples]
[2,000 more words of troubleshooting]
```

✅ **GOOD**:
```markdown
## TimeGPT API Reference

See: `{baseDir}/references/TIMEGPT_API.md` for complete API documentation.

Quick examples:
- [2-3 minimal examples, 200 words total]

For troubleshooting: `{baseDir}/references/000-docs/157-DR-FAQS-troubleshooting.md`
```

**Why this fails**: Context saturation, partial instruction execution, increased costs.

---

#### Anti-Pattern 3: Generic "Helps With Tasks" Descriptions
❌ **BAD**:
```yaml
description: Helps with time-series forecasting tasks and data analysis.
```

✅ **GOOD**:
```yaml
description: |
  Transforms user data into Nixtla-ready schema (unique_id, ds, y columns).
  Generates pandas/SQL transformation code and creates schema documentation.
  Use when onboarding new datasets, mapping client data, or preparing forecasts.
  Trigger with "map my data to Nixtla format", "prepare data for TimeGPT".
```

**Why this fails**: Vague triggers prevent accurate intent matching by Claude.

---

#### Anti-Pattern 4: Combining Metadata and Skill Prompt into Single Message
❌ **BAD** (internal implementation):
```javascript
{
  role: "user",
  isMeta: false,  // Trying to show both UI message AND skill content
  content: "<command-message>Loading...</command-message>\n\n[Full SKILL.md]"
}
```

✅ **GOOD**:
```javascript
// Message 1: UI indicator
{ role: "user", isMeta: false, content: "<command-message>..." }
// Message 2: Hidden skill content
{ role: "user", isMeta: true, content: "[Full SKILL.md]" }
```

**Why this fails**: Pollutes user's conversation view, violates transparency requirements.

---

#### Anti-Pattern 5: Overly Permissive Tool Access
❌ **BAD**:
```yaml
# Schema mapping skill that only reads files
allowed-tools: "Bash,Read,Write,Edit,Glob,Grep,WebSearch,Task,Agent"
```

✅ **GOOD**:
```yaml
# Schema mapping skill - read-only analysis
allowed-tools: "Read,Glob,Grep"
```

**Why this fails**: Unnecessary attack surface, violates principle of least privilege.

---

#### Anti-Pattern 6: Unscoped Bash Access
❌ **BAD**:
```yaml
# Experiment runner
allowed-tools: "Bash,Read,Write"  # Any bash command allowed!
```

✅ **GOOD**:
```yaml
# Experiment runner - Python scripts only
allowed-tools: "Bash(python:*),Bash(pip:*),Read,Write,Grep"
```

**Why this fails**: Opens door to arbitrary command execution.

---

#### Anti-Pattern 7: Missing Trigger Phrases
❌ **BAD**:
```yaml
description: Analyzes prediction markets using TimeGPT forecasting.
```

✅ **GOOD**:
```yaml
description: |
  Analyzes Polymarket contracts using TimeGPT forecasting.
  Use when forecasting prediction markets or analyzing contract odds.
  Trigger with "forecast Polymarket", "analyze prediction market prices".
```

**Why this fails**: Claude doesn't know which user phrases should activate the skill.

---

#### Anti-Pattern 8: Exceeding Description Budget
❌ **BAD** (40 skills × 600 chars = 24,000 chars):
```yaml
description: |
  [600 character verbose description per skill]
  [Result: Silent skill filtering, random activation failures]
```

✅ **GOOD** (40 skills × 350 chars = 14,000 chars):
```yaml
description: |
  [350 character focused description per skill]
  [Result: All skills discoverable, reliable activation]
```

**Why this fails**: Exceeds 15,000-char budget, causes silent filtering.

---

### Production Debugging Checklist for Nixtla

When skills fail unexpectedly, check in this order:

1. **Description budget**: `find .claude/skills/nixtla-*/SKILL.md -exec grep -A 5 '^description:' {} \; | wc -c`
2. **Frontmatter validity**: YAML parses correctly, required fields present
3. **Path references**: All `{baseDir}` substitutions resolve
4. **SKILL.md size**: Under 500 lines / 5,000 words
5. **Tool permissions**: `allowed-tools` includes necessary tools only
6. **Error code**: Check which of 5 validation errors is occurring
7. **Context saturation**: Too many skills invoked in one session

---

## 16. Development Methodology (Anthropic Engineering)

**⚠️ CRITICAL**: This is Anthropic's recommended workflow for building production skills.

### Evaluation-First Approach

**Official Guidance** (Anthropic Engineering):
> "Identify specific gaps in your agents' capabilities by running them on representative tasks and observing where they struggle or require additional context. Then build skills incrementally to address these shortcomings."

**Four-Step Workflow**:

#### Step 1: Run Representative Tasks
- Deploy Claude on actual user workflows (WITHOUT skills first)
- Use real production data, not synthetic examples
- Document every failure, struggle, or suboptimal output

**Nixtla Example**:
```
Task: "Forecast this e-commerce dataset with TimeGPT"
Claude without skills:
❌ Doesn't know TimeGPT schema requirements (unique_id, ds, y)
❌ Generates non-deterministic API calls (sometimes wrong)
❌ Can't remember fine-tuning best practices across conversations
```

#### Step 2: Observe Where Agents Struggle
- **Context gaps**: Missing domain knowledge (TimeGPT API patterns)
- **Reliability issues**: Non-deterministic code generation
- **Repetition**: Answering same questions across sessions

**Nixtla Observations**:
```
Struggle Pattern 1: Users repeatedly ask "how do I structure data for TimeGPT?"
→ Indicates need for: nixtla-schema-mapper skill

Struggle Pattern 2: Experiment workflows require multiple retry attempts
→ Indicates need for: nixtla-experiment-architect with pre-written scripts

Struggle Pattern 3: Fine-tuning parameters always need explaining
→ Indicates need for: nixtla-timegpt-finetune-lab with reference docs
```

#### Step 3: Build Skills Incrementally
- Start with ONE skill addressing the MOST COMMON gap
- Deploy to small user group
- Measure improvement
- Iterate

**Anti-Pattern**: Building all 40 skills upfront before testing any

**Nixtla Production Pattern**:
```
Week 1: Build nixtla-schema-mapper (most common question)
Week 2: Deploy to 10 beta users, measure schema error reduction
Week 3: Fix issues, expand to 50 users
Week 4: Build nixtla-experiment-architect (second most common struggle)
...iterate
```

#### Step 4: Claude-Assisted Skill Authoring

**Self-Reflection Pattern** (Anthropic Engineering):
> "Ask Claude to capture its successful approaches and common mistakes into reusable context and code within a skill."

**Workflow**:
1. Complete a successful task with Claude (e.g., run TimeGPT forecast)
2. Ask Claude: "What worked well in this workflow? What would you need to remember for next time?"
3. Ask Claude: "Draft a SKILL.md that captures this workflow"
4. Claude generates skill based on actual experience
5. Human reviews and refines

**Example Prompt for Nixtla**:
```
User: "We just successfully ran a TimeGPT fine-tuning job. Please capture
this workflow as a skill called 'nixtla-timegpt-finetune-lab'. Include:
- What worked well in our approach
- Common mistakes we avoided
- Key API patterns you used
- The validation scripts we ran
- What you'd want to remember for the next fine-tuning job"

Claude: [Generates complete SKILL.md based on session experience]
```

**Key Insight**: Claude learns what context it ACTUALLY needed vs what you THOUGHT it would need.

---

### Production Checklist for Nixtla Skill Development

**Before Building ANY Skill**:
- [ ] Identified specific task where Claude struggles consistently
- [ ] Observed pattern across multiple users/sessions
- [ ] Quantified impact (how many users hit this issue?)
- [ ] Confirmed skill would address >50% of observed struggles

**During Skill Development**:
- [ ] Started with Claude-assisted draft (self-reflection)
- [ ] Tested on actual failing workflows from Step 1
- [ ] Measured before/after success rate
- [ ] Iterated based on real usage data

**After Deployment**:
- [ ] Monitored skill activation rate (is Claude actually using it?)
- [ ] Tracked context budget impact (total description length)
- [ ] Collected user feedback on skill quality
- [ ] Scheduled quarterly review/refinement

**Warning Signs** (Poorly Designed Skills):
- ❌ Skill created without observing actual struggles
- ❌ Description doesn't match when Claude activates it
- ❌ Users manually invoke with `/skill-name` (Claude should auto-activate)
- ❌ Skill loaded but doesn't improve task success rate

---

### Naming Criticality (Anthropic Engineering)

**Official Guidance**:
> "Pay special attention to the `name` and `description` of your skill. Claude will use these when deciding whether to trigger the skill in response to its current task."

**Nixtla Production Pattern**:

| Skill Name | Description Must Trigger On | Anti-Pattern |
|------------|------------------------------|--------------|
| `nixtla-schema-mapper` | "map data to Nixtla format", "prepare for TimeGPT" | ❌ "data transformation" (too vague) |
| `nixtla-experiment-architect` | "run experiments", "compare models", "benchmark forecasts" | ❌ "help with experiments" (not actionable) |
| `nixtla-timegpt-finetune-lab` | "fine-tune TimeGPT", "train custom model" | ❌ "model training" (too generic) |

**Test**: If Claude doesn't auto-activate on expected user phrases, description needs revision.

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

**Last Updated**: 2025-12-08
**Maintained By**: Intent Solutions (Jeremy Longshore)
**Status**: AUTHORITATIVE - Single Source of Truth for Claude Skills Development

---

## Changelog

### Version 2.3.0 (2025-12-08) - Anthropic Engineering Blog Audit (FINAL)

**Audited Against**: [Anthropic Engineering Blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) - ENGINEERING SOURCE (oldest, deepest technical)

**CRITICAL ENGINEERING INSIGHTS** (Game-Changing for Nixtla):

1. **"Effectively Unbounded" Context Architecture** (Section 5)
   - Three-tier progressive disclosure: Metadata → SKILL.md → References
   - Only Tier 1 (description) counts against 15,000-char budget
   - Tier 2 & 3 load dynamically → "effectively unbounded" total content
   - **Nixtla Impact**: Bundle 43,000+ words of TimeGPT docs with zero context penalty

2. **Code Execution Performance Economics** (Executive Summary)
   - Deterministic code execution is **200x cheaper** than token generation for algorithmic tasks
   - Scripts consume ZERO context tokens (only output counts)
   - "Sorting via tokens is far more expensive than running a sorting algorithm"
   - **Nixtla Impact**: TimeGPT API loops, pandas transforms, validation scripts save massive costs

3. **Mutually Exclusive Contexts Pattern** (Section 5)
   - Split reference files when contexts are NEVER used together
   - Example: Forecasting vs Fine-tuning workflows (mutually exclusive)
   - **Context Savings**: 76% reduction (43,000 → 10,000 words loaded)
   - **Nixtla Impact**: Separate FORECASTING.md, FINETUNING.md, ANOMALY_DETECTION.md, TROUBLESHOOTING.md

4. **Evaluation-First Development Methodology** (New Section 16)
   - Official Anthropic workflow for building production skills
   - 4-Step Process: Run tasks → Observe struggles → Build incrementally → Claude-assisted authoring
   - **Anti-Pattern**: Building all 40 skills upfront before testing
   - **Nixtla Impact**: Identify which skills actually needed via user observation

5. **Self-Reflection Pattern for Skill Creation** (Section 16)
   - "Ask Claude to capture successful approaches and common mistakes into reusable skills"
   - Claude drafts SKILL.md based on actual session experience
   - **Key**: Learn what context Claude ACTUALLY needed vs what you thought
   - **Nixtla Workflow**: After successful TimeGPT job, ask Claude to draft the skill

6. **Naming Criticality for Auto-Activation** (Section 16)
   - "Pay special attention to name and description—Claude uses these to decide trigger"
   - **Test**: If Claude doesn't auto-activate on expected phrases, description needs revision
   - **Nixtla Example**: "map data to Nixtla format" must trigger nixtla-schema-mapper

**Production Checklist Added**:
- Before building: Observed struggles, quantified impact, confirmed >50% address rate
- During development: Claude-assisted draft, tested on failing workflows, measured success rate
- After deployment: Monitored activation rate, tracked context budget, scheduled quarterly review

**Warning Signs** (Poorly Designed Skills):
- ❌ Created without observing actual struggles
- ❌ Users manually invoke with /skill-name (should auto-activate)
- ❌ Loaded but doesn't improve success rate

**New Section**: 16. Development Methodology (Anthropic Engineering) - Complete production workflow

**Status**: ENGINEERING-COMPLETE - All three official sources integrated

---

### Version 2.2.0 (2025-12-08) - Official Anthropic Blog Audit

**Audited Against**: [Official Anthropic Skills Blog](https://claude.com/blog/skills) - PRIMARY SOURCE OF TRUTH

**CRITICAL ADDITIONS (Priority 1)**:

1. **Four Core Design Principles** (Executive Summary)
   - Composable: Multiple skills work together automatically
   - Portable: Same format across ALL platforms (apps/API/Code)
   - Efficient: Progressive disclosure, minimal context loading
   - Powerful: Executable code + prompts for complete workflows
   - **Nixtla Impact**: Architectural philosophy for all skill design decisions

2. **`/v1/skills` API Endpoint** (Section 2)
   - New programmatic skill control endpoint
   - Versioning and management capabilities
   - Separate from Messages API calls
   - **CRITICAL**: Required for Nixtla API integrations

3. **Code Execution Tool Beta Requirement** (Section 2)
   - **BLOCKER**: Skills with scripts require this beta feature
   - Must be enabled in API configuration
   - Provides secure sandbox for script execution
   - **Nixtla Impact**: TimeGPT/pandas/validation scripts won't work without it

4. **Official Pre-built Anthropic Skills** (Section 2)
   - Excel, PowerPoint, Word, Fillable PDFs
   - **Nixtla Strategy**: Leverage these instead of reinventing document processing

5. **Skill-Creator Interactive Tool** (Section 2)
   - Official Anthropic tool for guided skill creation
   - No manual file editing required
   - Available via `/skill-creator` command
   - **Nixtla Adoption**: Use for rapid prototyping

6. **Enterprise Admin Controls** (Section 2)
   - Team/Enterprise admins must enable skills organization-wide
   - Settings toggle at organization level
   - **Critical for Nixtla Enterprise Customers**: Requires admin approval

7. **Chain-of-Thought Visibility** (Section 1)
   - Users see skills in Claude's reasoning trace
   - Transparency, debuggability, trust
   - **Nixtla Impact**: Customers can audit which skills trigger

8. **Marketplace Plugin Distribution** (Section 2)
   - `anthropics/skills` marketplace for Claude Code
   - Managed updates and versioning
   - **Future Nixtla Strategy**: Publish as marketplace plugin

**API Integration Example Added**:
```python
# Deploy via /v1/skills endpoint
skill_response = client.skills.create(
    skill_content=skill_md_content,
    version="1.0.0"
)
```

**Production Requirements Documented**:
1. Request Code Execution Tool beta access
2. Implement `/v1/skills` deployment automation
3. Version all skills semantically
4. Test scripts in sandbox before production

**Status**: Complete alignment with official Anthropic sources

---

### Version 2.1.0 (2025-12-08) - Lee Han Chung Audit

**Audited Against**: [Lee Han Chung Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)

**Critical Additions**:
1. **Message Injection Architecture** (Section 1) - Details on `isMeta` true/false pattern, XML tags
2. **15,000-Char Description Budget** (Section 4) - Production constraint with scaling formulas
3. **Permissions Revert Lifecycle** (Section 6) - Temporary escalation clarification
4. **5,000-Word SKILL.md Limit** (Section 5) - Context saturation prevention
5. **Five Validation Error Codes** (Section 14) - Complete error handling guide
6. **Progressive Testing Workflow** (Section 14) - 5-step validation process
7. **Eight Critical Anti-Patterns** (Section 15) - Production debugging checklist

**Nixtla Production Enhancements**:
- Scalable skill portfolio guidance (removed hardcoded 11-skill assumption)
- Production monitoring bash commands
- Context budget formulas for growing skill counts
- Lifecycle examples with nixtla-specific skill names

**Status**: Production-ready for Nixtla internal team deployment

### Version 2.0.0 (2025-12-06) - Initial Consolidation

**Changes**:
- Consolidated 4 separate standards into single 65KB reference
- Added Appendix A (Frontmatter Schema), B (Authoring Guide), C (Nixtla Strategy)
- Created navigation README for skills-schema folder


---
# APPENDIX A: Frontmatter Schema Quick Reference
---



```yaml
---
# ═══════════════════════════════════════════════════════════════
# REQUIRED FIELDS
# ═══════════════════════════════════════════════════════════════

name: skill-name
# Type: string
# Max Length: 64 characters
# Constraints:
#   - Lowercase letters, numbers, and hyphens ONLY
#   - No XML tags
#   - Cannot contain reserved words: "anthropic", "claude"
# Purpose: Command identifier when Claude invokes the Skill tool
# Examples:
#   ✅ processing-pdfs
#   ✅ analyzing-spreadsheets
#   ✅ git-commit-helper
#   ❌ PDF_Processing (uppercase)
#   ❌ claude-helper (reserved word)
#   ❌ my skill (spaces)

description: >
  What this skill does. Key capabilities. Use when [scenarios].
  Trigger with "[phrase 1]", "[phrase 2]".
# Type: string
# Max Length: 1024 characters
# Constraints:
#   - Must be non-empty
#   - No XML tags
#   - MUST use THIRD PERSON voice (injected into system prompt)
# Purpose: Primary signal for Claude's skill selection
# Formula: [Capabilities]. [Features]. Use when [scenarios]. Trigger with "[phrases]".
# Examples:
#   ✅ "Extract text and tables from PDF files, fill forms, merge documents.
#       Use when working with PDF files or when the user mentions PDFs."
#   ✅ "Generate commit messages by analyzing git diffs. Use when writing
#       commit messages or reviewing staged changes."
#   ❌ "I can help you process PDFs" (first person)
#   ❌ "You can use this for data" (second person)
#   ❌ "Helps with documents" (too vague)

# ═══════════════════════════════════════════════════════════════
# OPTIONAL FIELDS
# ═══════════════════════════════════════════════════════════════

allowed-tools: "Read,Write,Glob,Grep,Edit"
# Type: CSV string
# Default: No pre-approved tools (user prompted for each)
# Purpose: Pre-approves tools SCOPED TO SKILL EXECUTION ONLY
# NOTE: Only supported in Claude Code, NOT claude.ai web version
# Syntax Examples:
#   "Read,Write,Glob,Grep,Edit"           # Multiple tools
#   "Bash(git:*),Read,Grep"               # Scoped bash (git only)
#   "Bash(npm:*),Bash(npx:*),Read"        # NPM-scoped
#   "Read,Glob,Grep"                      # Read-only audit

model: inherit
# Type: string
# Default: "inherit" (use session model)
# Purpose: Override session model for skill execution
# Examples:
#   inherit                               # Use current model (default)
#   "claude-opus-4-20250514"              # Force Opus
#   "claude-sonnet-4-20250514"            # Force Sonnet
#   "claude-haiku-3-20250514"             # Force Haiku

version: "1.0.0"
# Type: string (semver)
# Purpose: Version tracking for skill evolution
# Format: MAJOR.MINOR.PATCH
#   MAJOR = Breaking changes
#   MINOR = New features, additive
#   PATCH = Bug fixes, clarifications

license: "MIT"
# Type: string
# Purpose: License terms reference
# Examples:
#   "MIT"
#   "Apache-2.0"
#   "Proprietary - See LICENSE.txt"

mode: false
# Type: boolean
# Default: false
# Purpose: When true, skill appears in prominent "Mode Commands" UI section
# Use Case: Skills that transform Claude's behavior for extended sessions

disable-model-invocation: false
# Type: boolean
# Default: false
# Purpose: When true, removes skill from <available_skills> list
# Effect: Users must invoke manually via /skill-name
# Use Cases:
#   - Dangerous operations (deployments, deletions)
#   - Infrastructure skills
#   - Skills that should NEVER auto-activate

# ═══════════════════════════════════════════════════════════════
# UNDOCUMENTED/EXPERIMENTAL - AVOID IN PRODUCTION
# ═══════════════════════════════════════════════════════════════

# when_to_use: "Additional usage context"
# Status: UNDOCUMENTED - behavior may change without notice
# Behavior: Appends to description with hyphen separator
# Recommendation: Do NOT use. Rely on detailed description field instead.
---
```

---

## Field Reference Table

| Field | Required | Type | Max | Default | Purpose |
|-------|----------|------|-----|---------|---------|
| `name` | **YES** | string | 64 chars | - | Command identifier |
| `description` | **YES** | string | 1024 chars | - | Skill selection signal |
| `allowed-tools` | No | CSV | - | none | Pre-approved tools |
| `model` | No | string | - | `inherit` | Model override |
| `version` | No | semver | - | - | Version tracking |
| `license` | No | string | - | - | License reference |
| `mode` | No | boolean | - | `false` | Mode command flag |
| `disable-model-invocation` | No | boolean | - | `false` | Manual-only flag |

---

## Validation Rules

### Name Field

```
✅ VALID:
- processing-pdfs
- data-analysis-v2
- git-commit-helper
- bigquery-forecaster

❌ INVALID:
- PDF_Processing      → uppercase not allowed
- claude-helper       → reserved word "claude"
- my skill           → spaces not allowed
- anthropic-tools    → reserved word "anthropic"
- a                  → too short (use descriptive names)
- this-is-a-very-long-skill-name-that-exceeds-sixty-four-characters-limit → too long
```

### Description Field

```
✅ VALID (third person, specific, includes triggers):
"Analyzes Excel spreadsheets, creates pivot tables, generates charts.
 Use when analyzing Excel files, spreadsheets, or .xlsx files.
 Trigger with 'analyze this spreadsheet', 'create pivot table'."

❌ INVALID:
"I can help you with Excel"     → first person
"You can use this for data"     → second person
"Helps with documents"          → too vague
"Excel tool"                    → no triggers
```

### Allowed-Tools Syntax

```yaml
# Full tool access
allowed-tools: "Bash"                    # All bash commands (dangerous)

# Scoped tool access (RECOMMENDED)
allowed-tools: "Bash(git:*)"             # Only git commands
allowed-tools: "Bash(git status:*)"      # Only git status
allowed-tools: "Bash(npm:*),Bash(npx:*)" # Only npm/npx

# Multiple tools
allowed-tools: "Read,Write,Glob,Grep,Edit"

# Read-only
allowed-tools: "Read,Glob,Grep"
```

---

## Directory Structure

```
skill-name/
├── SKILL.md              # REQUIRED - Frontmatter + instructions
├── scripts/              # OPTIONAL - Executable code (no token cost)
│   ├── analyze.py
│   └── validate.py
├── references/           # OPTIONAL - Docs loaded into context
│   ├── API_REFERENCE.md
│   └── EXAMPLES.md
├── assets/               # OPTIONAL - Templates (path reference only)
│   └── report_template.md
└── LICENSE.txt           # OPTIONAL - License terms
```

### Token Cost by Directory

| Directory | Loaded Into Context? | Token Cost |
|-----------|---------------------|------------|
| `004-scripts/` | No (executed via Bash) | **None** |
| `references/` | Yes (via Read tool) | **High** |
| `assets/` | No (path reference only) | **None** |

---

## Minimal Valid SKILL.md

```yaml
---
name: my-skill
description: Does X and Y. Use when [condition]. Trigger with "phrase".
---

# My Skill

Instructions here.
```

---

## Complete Valid SKILL.md

```yaml
---
name: analyzing-spreadsheets
description: |
  Analyzes Excel spreadsheets, creates pivot tables, generates charts and reports.
  Use when working with Excel files, .xlsx data, or tabular analysis.
  Trigger with "analyze this spreadsheet", "create pivot table", "summarize Excel data".
allowed-tools: "Read,Write,Glob,Grep,Edit"
version: "1.0.0"
---

# Analyzing Spreadsheets

[Full instructions follow...]
```

---

## Sources

- [Official Anthropic Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Official Anthropic Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)

---

**Last Updated**: 2025-12-06
**Status**: CANONICAL - Cross-Repo Standard


---
# APPENDIX B: Authoring Guide & Patterns
---


## Quick Start Template

```yaml
---
name: your-skill-name
description: |
  [Primary capabilities]. [Secondary features].
  Use when [3-4 trigger scenarios].
  Trigger with "[phrase 1]", "[phrase 2]", "[phrase 3]".
allowed-tools: "Read,Write,Glob,Grep,Edit"
version: "1.0.0"
---

# [Skill Name]

[1-2 sentence purpose statement.]

## Overview

[3-5 sentences: what, when, capabilities, output]

## Prerequisites

**Required**:
- [Tool/package 1]: [Purpose]

**Environment Variables**:
- `ENV_VAR`: [Description]

## Instructions

### Step 1: [Action Verb]

[Imperative instructions]

### Step 2: [Action Verb]

[More instructions]

## Output

- **[Artifact 1]**: [Description]
- **[Artifact 2]**: [Description]

## Error Handling

1. **Error**: `[Message]`
   **Solution**: [Fix]

2. **Error**: `[Message]`
   **Solution**: [Fix]

## Examples

### Example 1: [Scenario]

**Input**: [Example]
**Output**: [Result]

## Resources

- Reference: `{baseDir}/references/API_REFERENCE.md`
- Script: `{baseDir}/scripts/validate.py`
```

---

## Writing Effective Descriptions

### The Formula

```
[Primary capabilities]. [Secondary features]. Use when [scenarios]. Trigger with "[phrases]".
```

### Quality Checklist

| Criterion | Weight | How to Achieve |
|-----------|--------|----------------|
| **Action-oriented** | 20% | Use strong verbs: "Generates", "Analyzes", "Transforms" |
| **Clear triggers** | 25% | Include "Use when [scenarios]" |
| **Comprehensive** | 15% | Cover what + when + scope |
| **Natural language** | 20% | Include phrases users actually say |
| **Specificity** | 10% | Be specific without being verbose |
| **Technical terms** | 10% | Use domain keywords users naturally use |

### Voice Rules

**ALWAYS use third person** - descriptions are injected into system prompt:

```yaml
# ✅ CORRECT (third person)
description: "Processes Excel files and generates reports"

# ❌ WRONG (first person)
description: "I can help you process Excel files"

# ❌ WRONG (second person)
description: "You can use this to process Excel files"
```

### Good vs Bad Examples

```yaml
# ✅ EXCELLENT (specific, triggers, third person)
description: |
  Analyzes Polymarket prediction market contracts using TimeGPT forecasting.
  Fetches contract odds, transforms to time series, generates price predictions.
  Use when analyzing prediction markets, forecasting contract prices.
  Trigger with 'forecast Polymarket', 'analyze prediction market'.

# ❌ BAD (vague, no triggers)
description: "Helps with prediction markets"

# ❌ BAD (too generic)
description: "Data analysis tool"
```

---

## Content Guidelines

### Size Limits

| Content | Target | Maximum |
|---------|--------|---------|
| SKILL.md body | ~300 lines | **500 lines** |
| Token budget | ~2,500 tokens | 5,000 tokens |
| Description | ~250 chars | 1,024 chars |

### Required Sections

1. **Purpose** (1-2 sentences)
2. **Overview** (3-5 sentences)
3. **Prerequisites** (tools, packages, env vars)
4. **Instructions** (step-by-step, imperative voice)
5. **Output** (what artifacts are produced)
6. **Error Handling** (4+ common failures with solutions)
7. **Examples** (2-3 concrete input/output pairs)
8. **Resources** (links to bundled files)

### Imperative Voice

Use imperative voice for instructions:

```markdown
# ✅ CORRECT (imperative)
### Step 1: Analyze the input data
Run the validation script to check data format.

# ❌ WRONG (passive/descriptive)
### Step 1: Input data analysis
The input data should be analyzed for format issues.
```

---

## Progressive Disclosure

### When to Split Content

Split SKILL.md when it exceeds **400 lines**:

**Pattern 1: High-level guide with references**
```markdown
# PDF Processing

## Quick start
[Basic instructions - 50 lines]

## Advanced features
**Form filling**: See [FORMS.md](FORMS.md)
**API reference**: See [REFERENCE.md](REFERENCE.md)
```

**Pattern 2: Domain-specific organization**
```
bigquery-skill/
├── SKILL.md (overview - 200 lines)
└── reference/
    ├── finance.md (revenue metrics)
    ├── sales.md (pipeline data)
    └── product.md (usage analytics)
```

### Critical Rule: One-Level-Deep References

**AVOID deeply nested references** - Claude may only partially read nested files.

```
# ❌ BAD (too deep)
SKILL.md → advanced.md → details.md → actual_info.md

# ✅ GOOD (one level)
SKILL.md → advanced.md
SKILL.md → reference.md
SKILL.md → examples.md
```

---

## Path References

### Always Use `{baseDir}`

**NEVER hardcode absolute paths** - breaks portability:

```markdown
# ✅ CORRECT
Run: `python {baseDir}/scripts/validate.py`
See: `{baseDir}/references/API_DOCS.md`

# ❌ WRONG
Run: `python /home/user/skills/my-skill/scripts/validate.py`
```

### Forward Slashes Only

```markdown
# ✅ CORRECT (works everywhere)
{baseDir}/scripts/helper.py

# ❌ WRONG (breaks on Unix)
{baseDir}\scripts\helper.py
```

---

## Security Best Practices

### Principle of Least Privilege

Grant ONLY tools the skill actually needs:

```yaml
# ✅ GOOD - Minimal necessary tools
allowed-tools: "Read,Glob,Grep"              # Read-only audit
allowed-tools: "Read,Write,Edit"             # File transformation
allowed-tools: "Bash(git:*),Read,Grep"       # Git operations only

# ❌ BAD - Overly permissive
allowed-tools: "Bash,Read,Write,Edit,Glob,Grep,WebSearch,Task,Agent"
allowed-tools: "Bash"                        # Unscoped = all commands
```

### When to Use `disable-model-invocation: true`

Set this flag for skills that:
- Perform **destructive operations** (delete files, drop databases)
- **Deploy to production**
- Access **sensitive credentials**
- Run **irreversible commands**
- Should **NEVER auto-activate**

```yaml
---
name: deploy-production
description: Deploy to production. Dangerous - requires explicit invocation.
disable-model-invocation: true
allowed-tools: "Bash(deploy:*),Read,Glob"
---
```

### Security Audit Checklist

Before using untrusted skills:
- [ ] Review all bundled files (SKILL.md, scripts, resources)
- [ ] Check for unusual network calls
- [ ] Inspect scripts for malicious code
- [ ] Verify tool invocations match stated purpose
- [ ] Validate external URLs (if any)

---

## Model Selection

### When to Override

| Scenario | Recommendation |
|----------|----------------|
| Most skills | `model: inherit` or omit |
| Complex reasoning | `claude-opus-4-*` |
| Fast, simple tasks | `claude-haiku-*` |
| Balanced | `claude-sonnet-4-*` |

### Testing Across Models

**Always test with all models you plan to use:**

- **Haiku**: Does the skill provide sufficient guidance?
- **Sonnet**: Is content clear and efficient?
- **Opus**: Are instructions avoiding over-explanation?

What works for Opus may need more detail for Haiku.

---

## Common Patterns

### Pattern 1: Script Automation

```markdown
### Step 1: Fetch Data
Run: `python {baseDir}/scripts/fetch_data.py --output data.json`

### Step 2: Transform
Run: `python {baseDir}/scripts/transform.py --input data.json`

### Step 3: Report
Run: `python {baseDir}/scripts/generate_report.py`
```

### Pattern 2: Validation Loop

```markdown
### Step 1: Make changes
Edit the configuration file.

### Step 2: Validate
Run: `python {baseDir}/scripts/validate.py`

### Step 3: Fix and repeat
If validation fails, fix issues and run validation again.
Only proceed when validation passes.
```

### Pattern 3: Workflow with Checklist

```markdown
## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Analyze input
- [ ] Step 2: Transform data
- [ ] Step 3: Validate output
- [ ] Step 4: Generate report
```
```

---

## Production Readiness Checklist

### Naming & Description

- [ ] `name` matches folder name (lowercase + hyphens)
- [ ] `name` under 64 characters
- [ ] `description` under 1024 characters
- [ ] `description` uses **third person** voice
- [ ] `description` includes what + when + trigger phrases
- [ ] No reserved words (`anthropic`, `claude`)

### Structure & Tools

- [ ] SKILL.md at root of skill folder
- [ ] Body under **500 lines**
- [ ] Uses `{baseDir}` for all paths
- [ ] No hardcoded absolute paths
- [ ] `allowed-tools` includes only necessary tools
- [ ] Forward slashes in all paths

### Instructions Quality

- [ ] Has all required sections
- [ ] Uses **imperative voice**
- [ ] **2-3 concrete examples** with input/output
- [ ] **4+ common errors** documented with solutions
- [ ] One-level-deep file references only

### Testing

- [ ] Tested with Haiku, Sonnet, and Opus
- [ ] Trigger phrases activate skill correctly
- [ ] Does NOT trigger on unrelated requests
- [ ] Scripts execute without errors
- [ ] Examples produce expected output

### Security

- [ ] No secrets or credentials in skill
- [ ] Tools appropriately scoped
- [ ] Dangerous operations require explicit invocation
- [ ] External dependencies audited

---

## Versioning

### Semantic Versioning

```
MAJOR.MINOR.PATCH
  │     │     └── Bug fixes, clarifications
  │     └──────── New features, additive changes
  └────────────── Breaking changes to interface
```

### Changelog in SKILL.md

```markdown
## Version History

- **v2.0.0** (2025-12-01): Breaking - Changed output format to JSON
- **v1.1.0** (2025-11-15): Added batch processing support
- **v1.0.0** (2025-11-01): Initial release
```

### Deprecation Strategy

1. Add deprecation notice to description:
   ```yaml
   description: "[DEPRECATED - Use new-skill instead] Original description..."
   ```
2. Set `disable-model-invocation: true`
3. Keep available for manual invocation during transition
4. Remove in next major version

---

## Critical Gotchas

1. **Skills NOT in system prompt** - They're in the tools array as part of Skill meta-tool

2. **NOT concurrency-safe** - Avoid simultaneous skill invocations

3. **`when_to_use` is undocumented** - Use detailed `description` instead

4. **Hardcoded paths break portability** - Always use `{baseDir}`

5. **Token budget filtering** - 15,000 chars total for all skill descriptions; verbose skills may be silently filtered

6. **One-level-deep references only** - Claude may partially read nested files

7. **`allowed-tools` only in Claude Code** - Not supported on claude.ai web version

---

## Sources

- [Official Anthropic Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Official Anthropic Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Lee Han Chung Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)

---

**Last Updated**: 2025-12-06
**Status**: CANONICAL - Cross-Repo Standard


---
# APPENDIX C: Nixtla Skills Strategy
---


---

## Executive Summary

This document defines the complete "Nixtla Skills Universe" - a portfolio of Claude Code skills that spans:
- **OSS adoption & education** (free users learning Nixtla libraries)
- **TimeGPT-paid "pro lab" tools** (paying customers getting production value)
- **Internal Nixtla GTM & reliability agents** (solutions engineering, SRE, sales enablement)

**Target**: 11 skills across 4 categories, prioritized P1 → P3
**Audience Matrix**: INT (internal) | OSS (open-source users) | PAY (TimeGPT customers)

---

## Skills Universe Overview

### Category Breakdown

| Category | Skills | Audience Focus | Business Impact |
|----------|--------|----------------|-----------------|
| **Foundation** | 2 | Everyone (INT, OSS, PAY) | Enable all other skills |
| **Core Builders** | 4 | PAY (primary), OSS (secondary) | Main value prop for TimeGPT users |
| **Education** | 2 | OSS (primary), PAY (secondary) | Adoption, marketing, "time-series school" |
| **Ops & GTM** | 3 | INT (primary), PAY (limited) | Internal efficiency, enterprise sales |

### Priority Distribution

- **P1** (Near-term): 5 skills - Foundation + Core builders
- **P1.5** (Early): 1 skill - Production pipelines
- **P2** (Mid-term): 4 skills - Education + optimization
- **P3** (Later): 1 skill - Vertical blueprints + incident SRE

---

## 1. Foundation & "Plumbing" Skills

*These are the foundation everything else sits on.*

---

### 1.1 nixtla-skills-bootstrap

**Audience**: INT ✅ | OSS ✅ | PAY ✅
**Priority**: P1
**Role**: One-shot setup skill

#### What It Does

Runs the Nixtla skills installer and narrates the process:

1. Executes `nixtla-skills init` / `update` in current repo
2. Explains in real-time:
   - "Cloning/updating Nixtla skills source..."
   - "Copying nixtla-* skills into .claude/skills/..."
   - "Installed skills: [list]"
3. Validates installation

#### Output

Working `.claude/skills/nixtla-*` directory in any project.

#### Business Value

- **For OSS**: Zero-friction onboarding to Nixtla ecosystem
- **For PAY**: Fast setup, professional experience
- **For INT**: Standardized deployment across customer projects

---

### 1.2 nixtla-timegpt-lab (Mode Skill)

**Audience**: INT ✅ | OSS ✅* | PAY ✅
**Priority**: P1
**Role**: Global "Nixtla-native" mode switcher

*\*OSS users get Nixtla library defaults even without TimeGPT key*

#### What It Does

Switches Claude into "Nixtla-native" mode for the session:

1. **Library Preferences**:
   - Prefer: `statsforecast`, `mlforecast`, `neuralforecast`, TimeGPT client
   - Avoid: Generic libraries (Prophet, ARIMA without Nixtla wrappers)

2. **Teaching Mode**:
   - Use Nixtla docs/teaching-guide concepts when explaining models/metrics
   - Default to Nixtla stacks when user says "build a forecast"

3. **Code Reasoning**:
   - Applies to all subsequent code generation in session
   - Suggests Nixtla patterns for data prep, CV, metrics

#### Business Value

- **For OSS**: "Nixtla-first" mindset → library adoption
- **For PAY**: Seamless TimeGPT integration by default
- **For INT**: Consistent Nixtla patterns across customer engagements

---

## 2. Core Builder Skills (For Users & Paying Customers)

*Main value props for TimeGPT + Nixtlaverse users.*

---

### 2.1 nixtla-schema-mapper

**Audience**: INT ✅ | OSS ✅ | PAY ✅
**Priority**: P1
**Role**: Get user data into Nixtla-ready schema fast

#### What It Does

1. **Data Inspection**:
   - Reads CSV/SQL/dbt model
   - Infers: `unique_id`, `ds`, `y`, exogenous features

2. **Code Generation**:
   - Pandas transform script OR
   - dbt/SQL model to produce Nixtla schema

3. **Documentation**:
   - Creates `NIXTLA_SCHEMA_CONTRACT.md` describing mapping
   - Includes validation rules, edge cases

#### Use Cases

- New TimeGPT users onboarding their first dataset
- Nixtla solution engineers migrating client data
- Self-serve data prep for OSS users

#### Business Value

- **For PAY**: Reduces onboarding time from weeks → hours
- **For OSS**: Lowers barrier to first forecast
- **For INT**: Standardized schema approach across customers

---

### 2.2 nixtla-experiment-architect

**Audience**: INT ✅ | OSS ✅** | PAY ✅
**Priority**: P1
**Role**: Build full benchmark harness

*\*\*OSS version treats TimeGPT as optional candidate model*

#### What It Does

1. **Config Setup**:
   - Asks: dataset path/table, target, horizon, freq
   - Creates/extends `forecasting/config.yml`:
     - Targets, freq, horizon, metrics, CV strategy

2. **Experiment Generation**:
   - Creates `forecasting/experiments.py`:
     - **StatsForecast models**: AutoARIMA, AutoETS, AutoCES, Theta, intermittent, multi-seasonal
     - **MLForecast pipelines**: Global ML models
     - **TimeGPT calls**: via `NixtlaClient` (PAY) or stubbed (OSS)
     - **Cross-validation**: Time-aware CV + metrics table

3. **Results Framework**:
   - Metrics comparison table (sMAPE, MASE, MAE, etc.)
   - Model ranking by accuracy/speed/cost

#### OSS vs PAY Behavior

- **PAY**: Wires real TimeGPT API calls
- **OSS**: TimeGPT calls guarded/stubbed, focus on baselines + ML

#### Business Value

**Single highest-impact skill for external devs.**

- **For PAY**: Proves TimeGPT value with their data
- **For OSS**: Complete forecasting lab without API costs
- **For INT**: Reusable benchmark framework for every customer

---

### 2.3 nixtla-timegpt-finetune-lab

**Audience**: INT ✅ | OSS ❌ | PAY ✅
**Priority**: P2 (after Experiment Architect is solid)
**Role**: Help users set up TimeGPT fine-tuning projects

#### What It Does

1. **Data Splitting**:
   - Define train/val/test splits appropriate for time series
   - Handles multiple series, hierarchical structures

2. **Fine-Tune Generation**:
   - Creates `forecasting/timegpt_finetune_job.py`:
     - Data prep for fine-tuning API
     - Fine-tune job submission
     - Model registry/versioning

3. **Comparison Framework**:
   - Hooks into `experiments.py` to compare:
     - TimeGPT zero-shot
     - TimeGPT fine-tuned
     - Classical/ML baselines

4. **Documentation**:
   - `FINE_TUNE_README.md` explaining:
     - How to launch fine-tune
     - How to re-evaluate
     - When fine-tuning makes sense

#### Business Value

**"Next-level deep" for premium users.**

- **For PAY**: Premium feature, justifies higher pricing
- **For INT**: Advanced customer success playbook
- **Not for OSS**: Requires paid TimeGPT API

---

### 2.4 nixtla-prod-pipeline-generator

**Audience**: INT ✅ | OSS (limited) | PAY ✅
**Priority**: P1.5 (early, after schema/experiment MVP works)
**Role**: Turn experiments into production pipelines

#### What It Does

1. **Pipeline Detection**:
   - Reads `forecasting/config.yml` + experiment results
   - Asks: Airflow? Prefect? dbt? Plain cron?

2. **Orchestration Code Generation**:
   - Creates `pipelines/` directory with:
     - DAG/flow definition (orchestration-specific)
     - Data loading from Nixtla schema
     - TimeGPT and/or StatsForecast/MLForecast calls
     - Forecast output + metadata logging

3. **Monitoring Setup**:
   - Creates `monitoring.py`:
     - Rolling backtests
     - Drift/anomaly checks
     - Fallback to baselines on TimeGPT failure

4. **Documentation**:
   - Deployment guide
   - Monitoring dashboard setup
   - Runbook for common issues

#### OSS vs PAY Behavior

- **PAY**: Full TimeGPT production integration
- **OSS**: Limited to StatsForecast/MLForecast pipelines

#### Business Value

**Shows "we don't just benchmark, we help you ship."**

- **For PAY**: Complete production onboarding
- **For INT**: Repeatable deployment pattern
- **For OSS**: Production-grade open-source pipelines

---

## 3. Education & Onboarding Skills

*Targeted to OSS + PAY for adoption and marketing value.*

---

### 3.1 nixtla-tutor (Teaching Guide Skill)

**Audience**: INT ✅ | OSS ✅ | PAY ✅
**Priority**: P2
**Role**: Teach Nixtla model families like a guided course

#### What It Does

1. **Persona Detection**:
   - Identifies: Data scientist? PM? Engineer?
   - Tailors teaching style accordingly

2. **Curriculum Delivery**:
   - Walks through:
     - Baselines vs classical vs ML vs TimeGPT
     - When to use what
     - Model selection decision trees
   - Uses Nixtla teaching guide + docs

3. **Interactive Exercises**:
   - Small exercises using user's own code/data
   - Optional: generates "lesson notebooks" tailored to repo

4. **Progress Tracking**:
   - Remembers what's been covered
   - Suggests next topics

#### Business Value

**Aligns with "we are the time-series school" positioning.**

- **For OSS**: Educational content marketing
- **For PAY**: Premium onboarding experience
- **For INT**: Standardized training material

---

### 3.2 nixtla-docs-to-experiments

**Audience**: INT ✅ | OSS ⚪ | PAY ⚪
**Priority**: P2–P3
**Role**: Turn doc snippets into tested experiments

#### What It Does

1. **Input Processing**:
   - Takes markdown/doc snippet describing a method
   - Example: "intermittent demand forecasting with ADIDA"

2. **Code Generation**:
   - Produces runnable experiment scripts
   - Includes minimal tests ensuring examples stay in sync

3. **Documentation Sync**:
   - Creates `experiments/from_docs/` directory
   - Links back to original docs

#### Business Value

- **For INT**: De-risks docs drift, keeps examples trustworthy
- **For OSS/PAY**: More reliable example code

---

## 4. Observability, Optimization & GTM Skills

*More for Nixtla's own team + enterprise-facing work.*

---

### 4.1 nixtla-usage-optimizer

**Audience**: INT ✅ | OSS ❌ | PAY ✅ (as review service)
**Priority**: P2
**Role**: Audit usage and propose optimizations

#### What It Does

1. **Code Scanning**:
   - Finds where TimeGPT is used
   - Finds where StatsForecast/MLForecast/NeuralForecast are used
   - Optionally ingests usage logs/metrics

2. **Analysis**:
   - Where TimeGPT is overkill (cheap baseline OK)
   - Where TimeGPT should be used more
   - Recommended routing rules
   - Guardrail/fallback patterns

3. **Report Generation**:
   - Creates `nixtla_usage_report.md`:
     - Cost optimization opportunities
     - Accuracy improvement opportunities
     - Risk mitigation recommendations

#### Business Value

**Internal CSM/solutions tool OR premium review offering.**

- **For INT**: Customer success playbook
- **For PAY**: Premium "optimization review" service
- **For OSS**: Not applicable (no usage logs)

---

### 4.2 nixtla-vertical-blueprint

**Audience**: INT ✅ | OSS ❌ | PAY ✅ (indirectly)
**Priority**: P3
**Role**: Generate vertical solution skeletons

#### What It Does

1. **Vertical Selection**:
   - Choose: Retail? Energy? Fintech? Pharma? Manufacturing?
   - Input sample schema for vertical

2. **Architecture Generation**:
   - Creates `verticals/<vertical>/ARCHITECTURE.md`:
     - Data sources (typical for vertical)
     - Nixtla components (which models/methods)
     - Monitoring/alerting patterns

3. **Starter Code**:
   - Notebooks/pipelines specific to vertical
   - Example datasets (if available)

4. **ROI Story**:
   - Boilerplate for sales decks
   - Typical metrics for vertical
   - Success stories template

#### Business Value

**Part GTM, part solution engineering.**

- **For INT**: Accelerates vertical GTM
- **For PAY**: Faster enterprise onboarding
- **For OSS**: Not applicable

---

### 4.3 nixtla-incident-sre (Optional Later)

**Audience**: INT ✅ | OSS ❌ | PAY ❌
**Priority**: P3
**Role**: Help SRE respond to production incidents

#### What It Does

1. **Log Ingestion**:
   - Reads logs on:
     - Error spikes
     - Accuracy drops
     - Latency/cost anomalies

2. **Root Cause Suggestions**:
   - Where to roll back to baselines
   - Which configs changed recently
   - What experiments to re-run

3. **Runbook Generation**:
   - Creates incident response guide
   - Links to relevant experiments/configs

#### Business Value

**Internal ops agent for Nixtla reliability.**

- **For INT**: SRE efficiency
- **For OSS/PAY**: Not applicable (internal only)

---

## Complete Skills Matrix

| Skill | INT | OSS | PAY | Priority | Category |
|-------|-----|-----|-----|----------|----------|
| **nixtla-skills-bootstrap** | ✅ | ✅ | ✅ | P1 | Foundation |
| **nixtla-timegpt-lab** | ✅ | ✅* | ✅ | P1 | Foundation |
| **nixtla-schema-mapper** | ✅ | ✅ | ✅ | P1 | Core Builder |
| **nixtla-experiment-architect** | ✅ | ✅** | ✅ | P1 | Core Builder |
| **nixtla-prod-pipeline-generator** | ✅ | Limited | ✅ | P1.5 | Core Builder |
| **nixtla-timegpt-finetune-lab** | ✅ | ❌ | ✅ | P2 | Core Builder |
| **nixtla-tutor** | ✅ | ✅ | ✅ | P2 | Education |
| **nixtla-docs-to-experiments** | ✅ | ⚪ | ⚪ | P2–3 | Education |
| **nixtla-usage-optimizer** | ✅ | ❌ | ✅ (review) | P2 | Ops & GTM |
| **nixtla-vertical-blueprint** | ✅ | ❌ | ✅ (via Nixtla) | P3 | Ops & GTM |
| **nixtla-incident-sre** | ✅ | ❌ | ❌ | P3 | Ops & GTM |

**Legend**:
- ✅ = Full support
- ✅* = Works in OSS mode (Nixtla libraries, TimeGPT optional)
- ✅** = TimeGPT treated as optional candidate model
- ⚪ = Limited/indirect value
- ❌ = Not applicable

---

## Phased Rollout Strategy

### Phase 0: Foundation (Week 1-2)
**Goal**: Enable all other skills

- ✅ nixtla-skills-bootstrap
- ✅ nixtla-timegpt-lab

**Deliverable**: Any user can install Nixtla skills and enter "Nixtla mode"

---

### Phase 1: Core Builder MVP (Week 3-6)
**Goal**: Prove TimeGPT value with user data

- ✅ nixtla-schema-mapper
- ✅ nixtla-experiment-architect

**Deliverable**:
- Users can prep their data
- Users can run full benchmark (baselines + ML + TimeGPT)
- Clear accuracy comparison

---

### Phase 1.5: Production Path (Week 7-10)
**Goal**: Show "we help you ship"

- ✅ nixtla-prod-pipeline-generator

**Deliverable**:
- Users can deploy TimeGPT to production
- Monitoring + fallback patterns included

---

### Phase 2: Education & Optimization (Week 11-16)
**Goal**: Deepen adoption and engagement

- ✅ nixtla-tutor
- ✅ nixtla-timegpt-finetune-lab (PAY only)
- ✅ nixtla-usage-optimizer (INT + PAY)

**Deliverable**:
- Guided learning experience
- Advanced fine-tuning for premium users
- Cost optimization playbook

---

### Phase 3: Vertical GTM & Ops (Week 17+)
**Goal**: Enterprise sales enablement + internal reliability

- ✅ nixtla-vertical-blueprint
- ✅ nixtla-docs-to-experiments
- ✅ nixtla-incident-sre

**Deliverable**:
- Vertical solution templates
- Reliable docs examples
- Internal SRE tooling

---

## Business Impact Summary

### For OSS Users (Adoption & Education)
**Skills**: 6 (bootstrap, mode, schema, experiment, tutor, docs-to-experiments)

**Value**:
- Zero-friction onboarding
- Complete forecasting lab
- Educational content
- "Time-series school" positioning

**Conversion Path**: OSS → PAY when they need TimeGPT scale/accuracy

---

### For TimeGPT Paying Customers (Production Value)
**Skills**: 9 (all core builders + optimization)

**Value**:
- Fast onboarding (schema mapper)
- Proven accuracy (experiment architect)
- Production deployment (pipeline generator)
- Advanced features (fine-tuning)
- Cost optimization (usage optimizer)
- Premium review service

**Retention**: Customers get more value from TimeGPT investment

---

### For Nixtla Internal (Efficiency & GTM)
**Skills**: All 11

**Value**:
- Solution engineering productivity (2-3x faster)
- Customer success playbooks
- Vertical GTM acceleration
- Sales enablement (ROI stories)
- SRE reliability tooling

**Impact**: Team can support 5-10x more customers

---

## Success Metrics

### Adoption Metrics (OSS)
- Skills installation rate (bootstrap)
- Session mode activation (timegpt-lab)
- Experiment creation rate (experiment-architect)
- Tutorial completion rate (nixtla-tutor)

### Conversion Metrics (OSS → PAY)
- TimeGPT trial starts from OSS users
- Experiment → TimeGPT upgrade rate
- Fine-tuning adoption (PAY only feature)

### Retention Metrics (PAY)
- Production pipeline deployments
- Usage optimization reviews conducted
- Customer-reported time savings
- Churn reduction in TimeGPT customers

### Internal Metrics (INT)
- Customer onboarding time (target: 50% reduction)
- Solution engineer capacity (target: 3x projects/engineer)
- Vertical GTM velocity (time to first vertical deal)
- SRE incident resolution time

---

## Competitive Differentiation

### vs Prophet/ARIMA (OSS)
**Nixtla Advantage**:
- Comprehensive skill ecosystem
- Guided learning (nixtla-tutor)
- Production-ready pipelines
- "Time-series school" positioning

### vs Forecast.io, DataRobot (Commercial)
**Nixtla Advantage**:
- Open-source foundation (OSS skills work without API)
- Developer-first (Claude Code integration)
- Transparent experimentation (experiment-architect)
- Flexible deployment (not locked to platform)

### vs Building In-House
**Nixtla Advantage**:
- Pre-built skills (weeks → hours)
- Battle-tested patterns (schema, pipelines, monitoring)
- Ongoing updates (skills evolve with Nixtla libraries)
- ROI calculator (usage-optimizer)

---

## Next Steps

### For Immediate Implementation
1. **Create skills repository structure** (`nixtla-claude-skills/`)
2. **Implement Phase 0** (bootstrap + mode skills)
3. **Test with pilot users** (Nixtla team + 2-3 friendly customers)
4. **Document skill API contracts** (input/output specs)

### For Max (Decision Point)
1. **Review this strategy document**
2. **Prioritize audience**: OSS adoption vs PAY retention vs INT efficiency
3. **Budget allocation**: Which phases to fund in Q1 2026
4. **Success criteria**: What metrics matter most

### For Future Expansion
1. **Community contributions** (OSS skills from users)
2. **Marketplace positioning** (Claude Code plugin hub)
3. **Enterprise packaging** (skills + support SLA)
4. **Vertical expansion** (more verticals in Phase 3)

---

## Questions for Max

1. **Audience Priority**: OSS adoption vs PAY retention vs INT efficiency?
2. **Timeline**: Full rollout (16+ weeks) or MVP only (6-8 weeks)?
3. **Resources**: Build in-house vs partner with Intent Solutions?
4. **Packaging**: Free OSS skills + premium PAY skills? Or all free with TimeGPT upsell?
5. **Success Definition**: What does "skills success" look like in 6 months?

---

## Appendices

### A. Skills Naming Convention
- `nixtla-<domain>-<role>` (e.g., `nixtla-timegpt-lab`, `nixtla-schema-mapper`)
- Domain: `timegpt`, `schema`, `experiment`, `prod`, `tutor`, `usage`, `vertical`, `incident`
- Role: `lab`, `mapper`, `architect`, `generator`, `optimizer`, `blueprint`, `sre`

### B. Technical Architecture
- **Skill Type**: Agent skills (not just prompt templates)
- **Dependencies**: Nixtla libraries, Claude Code SDK
- **Storage**: `.claude/skills/nixtla-*/`
- **Activation**: Auto-trigger or manual `/skill nixtla-*`

### C. Documentation Structure
```
nixtla-claude-skills/
├── README.md (this strategy)
├── skills/
│   ├── nixtla-skills-bootstrap/
│   ├── nixtla-timegpt-lab/
│   ├── nixtla-schema-mapper/
│   └── ... (11 total)
├── docs/
│   ├── SKILL_API_CONTRACTS.md
│   ├── INSTALLATION_GUIDE.md
│   └── CONTRIBUTION_GUIDE.md
└── examples/
    └── (per-skill examples)
```

---

**Last Updated**: 2025-11-30
**Status**: Canonical Strategy - Awaiting Max's Review
**Next Review**: After Phase 0 implementation (2 weeks)

