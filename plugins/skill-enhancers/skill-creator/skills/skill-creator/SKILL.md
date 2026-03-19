---
name: skill-creator
description: |
  Create production-grade agent skills aligned with the 2026 AgentSkills.io spec and Anthropic
  best practices. Also validates existing skills against the Intent Solutions 100-point rubric.
  Use when building, testing, validating, or optimizing Claude Code skills.
  Trigger with "/skill-creator", "create a skill", "validate my skill", or "check skill quality".
  Make sure to use this skill whenever creating a new skill, slash command, or agent capability.
allowed-tools: "Read,Write,Edit,Glob,Grep,Bash(mkdir:*),Bash(chmod:*),Bash(python:*),Bash(claude:*),Task,AskUserQuestion"
version: 5.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
tags: [skill-creation, validation, meta-tooling]
model: inherit
---

# Skill Creator

Creates complete, spec-compliant skill packages following AgentSkills.io and Anthropic standards.
Supports both creation and validation workflows with 100-point marketplace grading.

## Overview

Skill Creator solves the gap between writing ad-hoc agent skills and producing marketplace-ready
packages that score well on the Intent Solutions 100-point rubric. It enforces the 2026 spec
(top-level identity fields, `${CLAUDE_SKILL_DIR}` paths, scored sections) and catches
contradictions that would cost marketplace points. Supports two modes: create new skills from
scratch with full validation, or grade/audit existing skills with actionable fix suggestions.

## Table of Contents

- [Instructions](#instructions) — Create mode (Steps 1-10) + Mode Detection
- [Validation Workflow](#validation-workflow) — Grade/audit existing skills (Steps V1-V5)
- [Examples](#examples) — Create, full package, and validate examples
- [Edge Cases](#edge-cases) — Name conflicts, long content, legacy metadata
- [Error Handling](#error-handling) — Common errors and solutions
- [Resources](#resources) — Reference files and scripts
- [Running and Evaluating Test Cases](#running-and-evaluating-test-cases) — Subagent-based eval with viewer
- [Improving the Skill](#improving-the-skill) — Iteration loop based on feedback
- [Description Optimization (Automated)](#description-optimization-automated) — Automated trigger accuracy tuning
- [Advanced: Blind Comparison](#advanced-blind-comparison) — A/B testing between skill versions
- [Packaging](#packaging) — Create distributable .skill files
- [Platform-Specific Notes](#platform-specific-notes) — Claude.ai and Cowork adaptations

## Instructions

### Mode Detection

Determine user intent from their prompt:
- **Create mode**: "create a skill", "build a skill", "new skill" -> proceed to Step 1
- **Validate mode**: "validate", "check", "grade", "score", "audit" -> jump to Validation Workflow

### Step 1: Understand Requirements

Ask the user with AskUserQuestion:

**Skill Identity:**
- Name (kebab-case, gerund preferred: `processing-pdfs`, `analyzing-data`)
- Purpose (1-2 sentences: what it does + when to use it)

**Execution Model:**
- User-invocable via `/name`? Or background knowledge only?
- Accepts arguments? (`$ARGUMENTS` substitution)
- Needs isolated context? (`context: fork` for subagent execution)
- Explicit-only invocation? (`disable-model-invocation: true` — prevents auto-activation, requires `/name`)

**Required Tools:**
- Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, Task, AskUserQuestion, Skill
- Bash must be scoped: `Bash(git:*)`, `Bash(npm:*)`, etc.
- MCP tools: `ServerName:tool_name`

**Complexity:**
- Simple (SKILL.md only)
- With scripts (automation code in `scripts/`)
- With references (documentation in `references/`)
- With templates (boilerplate in `templates/`)
- Full package (all directories)

**Location:**
- Global: `~/.claude/skills/<skill-name>/`
- Project: `.claude/skills/<skill-name>/`

### Step 2: Plan the Skill

Before writing, determine:

**Degrees of Freedom:**
| Level | When to Use |
|-------|-------------|
| High | Creative/open-ended tasks (analysis, writing) |
| Medium | Defined workflow, flexible content (most skills) |
| Low | Strict output format (compliance, API calls, configs) |

**Workflow Pattern** (see `${CLAUDE_SKILL_DIR}/references/workflows.md`):
- Sequential: fixed steps in order
- Conditional: branch based on input
- Wizard: interactive multi-step gathering
- Plan-Validate-Execute: verifiable intermediates
- Feedback Loop: iterate until quality met
- Search-Analyze-Report: explore and summarize

**Output Pattern** (see `${CLAUDE_SKILL_DIR}/references/output-patterns.md`):
- Strict template (exact format)
- Flexible template (structure with creative content)
- Examples-driven (input/output pairs)
- Visual (HTML generation)
- Structured data (JSON/YAML)

### Step 3: Initialize Structure

Create the skill directory and files:

```bash
mkdir -p {location}/{skill-name}
mkdir -p {location}/{skill-name}/scripts      # if needed
mkdir -p {location}/{skill-name}/references   # if needed
mkdir -p {location}/{skill-name}/templates    # if needed
mkdir -p {location}/{skill-name}/assets       # if needed
mkdir -p {location}/{skill-name}/evals        # for eval-driven development
```

### Step 4: Write SKILL.md

Generate the SKILL.md using the template from `${CLAUDE_SKILL_DIR}/templates/skill-template.md`.

**Frontmatter rules** (see `${CLAUDE_SKILL_DIR}/references/frontmatter-spec.md`):

Required fields:
```yaml
name: {skill-name}          # Must match directory name
description: |               # Third person, what + when + keywords
  {What it does}. Use when {scenario}.
  Trigger with "/{skill-name}" or "{natural phrase}".
```

Identity fields (top-level — marketplace validator scores these here):
```yaml
version: 1.0.0
author: {name} <{email}>
license: MIT
```

**IMPORTANT**: `version`, `author`, `license`, `tags`, and `compatible-with` are TOP-LEVEL fields.
Do NOT nest them under `metadata:`. The marketplace 100-point validator checks them at top-level.

Recommended fields:
```yaml
allowed-tools: "{scoped tools}"
model: inherit
```

Optional Claude Code extensions:
```yaml
argument-hint: "[arg]"              # If accepts $ARGUMENTS
context: fork                       # If needs isolated execution
agent: general-purpose              # Subagent type (with context: fork)
disable-model-invocation: true      # If explicit /name only (no auto-activation)
user-invocable: false               # If background knowledge only
compatibility: "Python 3.10+"      # If environment-specific
compatible-with: claude-code, codex # Platforms this works on
tags: [devops, ci]                  # Discovery tags
```

**Description writing — maximize discoverability scoring:**

Descriptions determine activation AND marketplace grade. "Use when"/"Trigger with" scoring is enterprise-tier only (marketplace grading). Standard tier does not penalize for missing these patterns. However, they remain best practices for discoverability regardless of tier.

```yaml
# Good - scores +6 pts on enterprise marketplace grading
description: |
  Analyze Python code for security vulnerabilities. Use when reviewing code
  before deployment. Trigger with "/security-scan" or "scan for vulnerabilities".

# Acceptable at standard tier, but loses 6 pts at enterprise tier
description: |
  Analyzes code for security issues.
```

Pattern (enterprise): "Use when [scenario]" (+3 pts) + "Trigger with [phrases]" (+3 pts) + "Make sure to use whenever..." for aggressive claiming.

**Token budget awareness:** All installed skill descriptions load at startup (~100 tokens each). The total skill list is capped at ~15,000 characters (`SLASH_COMMAND_TOOL_CHAR_BUDGET`). Keep descriptions impactful but efficient.

**Body content guidelines — section recommendations:**

Anthropic's spec places no format restrictions on body content. The sections below are enterprise-tier quality recommendations scored by the Intent Solutions marketplace rubric. At standard tier, these are not required but are still good practice:
```
## Overview       (>50 chars content: +4 pts enterprise)
## Prerequisites  (+2 pts enterprise)
## Instructions   (numbered steps: +3 pts enterprise)
## Output         (+2 pts enterprise)
## Error Handling (+2 pts enterprise)
## Examples       (+2 pts enterprise)
## Resources      (+1 pt enterprise)
5+ sections total: +2 pts bonus (enterprise)
```

Additional guidelines:
- Keep under 500 lines (offload to `references/` if longer)
- Concise — Claude is smart, don't over-explain
- Concrete examples over abstract descriptions
- Reference supporting files with relative markdown links: `[details](reference.md)` or `[API](references/api.md)` — Claude reads these on demand
- Use `${CLAUDE_SKILL_DIR}/` in DCI/bash contexts only: `` !`cat ${CLAUDE_SKILL_DIR}/references/small.md` ``
- Sections >20 lines (Output, Error Handling, Examples) → offload to `references/` with relative links
- If skill has 3+ distinct user operations → split into individual `commands/*.md` files
- Add DCI for common discovery: file existence checks, git status, tool version detection
- Include edge cases that actually matter
- No time-sensitive information
- Consistent terminology throughout

**String substitutions available:**
- `$ARGUMENTS` / `$0`, `$1` - user-provided arguments (pair with `argument-hint` frontmatter)
- `${CLAUDE_SESSION_ID}` - current session identifier

**Dynamic Context Injection (DCI):**
DCI runs shell commands BEFORE Claude sees the skill content, injecting output verbatim. This eliminates discovery tool calls — Claude starts with context already loaded.

Syntax: `` !`command` `` on its own line (Anthropic preprocessing spec).

Best practices:
- Add a `## Current State` section with DCI directives right after the title
- Always use fallbacks: `` !`terraform version 2>/dev/null || echo 'not installed'` ``
- Keep injections small — summaries and version info, not full file contents
- For skills that typically run 3+ discovery commands first, DCI saves those entire tool call rounds

Example:
```markdown
## Current State
!`git status --short`
!`git log --oneline -5`
!`node -v 2>/dev/null || echo 'N/A'`
```

### Step 5: Create Supporting Files

**Scripts** (`scripts/`):
- Scripts should solve problems, not punt to Claude
- Explicit error handling
- No voodoo constants (document all magic values)
- List required packages
- Make executable: `chmod +x scripts/*.py`

**References** (`references/`):
- Heavy documentation that doesn't need to load at activation
- TOC for files >100 lines
- One-level-deep references only (no `references/sub/dir/`)

**Templates** (`templates/`):
- Boilerplate files used for generation
- Use clear variable syntax (`{{VARIABLE_NAME}}`)

**Assets** (`assets/`):
- Static resources (images, configs, data files)

### Step 6: Validate

Run validation (see `${CLAUDE_SKILL_DIR}/references/validation-rules.md`):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate-skill.py {skill-dir}/SKILL.md
python3 ${CLAUDE_SKILL_DIR}/scripts/validate-skill.py --grade {skill-dir}/SKILL.md
```

Standard tier is the default (no required fields, broad compatibility). Use `--enterprise` for full 100-point marketplace grading.

**Validation checks:**
- Frontmatter: required fields, types, constraints
- Description: third person, what + when, keywords, length
- Body: under 500 lines, no absolute paths, has instructions + examples
- Tools: valid names, scoped Bash
- Resources: all `${CLAUDE_SKILL_DIR}/` references exist
- Anti-patterns: Windows paths, nested refs, hardcoded model IDs
- Progressive disclosure: appropriate use of references/

**If validation fails:** fix issues and re-run. Common fixes:
- Scope Bash tools: `Bash(git:*)` not `Bash`
- Remove absolute paths, use `${CLAUDE_SKILL_DIR}/`
- Split long SKILL.md into references
- Add missing sections (Overview, Prerequisites, Output)
- Move author/version to top-level if nested in metadata

### Step 7: Test & Evaluate

Create `evals/evals.json` with minimum 3 scenarios: happy path, edge case, negative test.

```json
[
  {"name": "basic_usage", "prompt": "Trigger prompt", "assertions": ["Expected behavior"]},
  {"name": "edge_case", "prompt": "Edge case prompt", "assertions": ["Expected handling"]},
  {"name": "negative_test", "prompt": "Should NOT trigger", "assertions": ["Skill inactive"]}
]
```

Run parallel evaluation: Claude A with skill installed vs Claude B without. Compare outputs against assertions — the skill should produce meaningfully better results for its target use cases.

### Step 8: Iterate

1. Review which assertions passed/failed
2. Modify SKILL.md instructions, examples, or constraints
3. Re-validate with `validate-skill.py --grade`
4. Re-test evals until all assertions pass

Common fixes: undertriggering -> pushier description, wrong format -> explicit output examples, over-constraining -> increase degrees of freedom.

### Step 9: Optimize Description

Create 20 trigger evaluation queries (10 should-trigger, 10 should-not-trigger). Split into train (14) and test (6) sets. Iterate description until >90% accuracy on both sets.

Tips: front-load distinctive keywords, include specific file types/tools/domains, add "Use when...", "Trigger with...", "Make sure to use whenever..." patterns. Avoid generic terms that overlap with other skills.

### Step 10: Report

Show the user:
```
SKILL CREATED
====================================

Location: {full path}

Files:
  SKILL.md ({lines} lines)
  scripts/{files}
  references/{files}
  templates/{files}
  evals/evals.json

Validation: Enterprise tier
  Errors: {count}
  Warnings: {count}
  Disclosure Score: {score}/6
  Grade: {letter} ({points}/100)

Eval Results:
  Scenarios: {count}
  Passed: {count}/{count}
  Description Accuracy: {percentage}%

Usage:
  /{skill-name} {argument-hint}
  or: "{natural language trigger}"

====================================
```

## Validation Workflow

When the user wants to validate, grade, or audit an existing skill:

### Step V1: Locate the Skill

Ask for the SKILL.md path or detect from context. Common locations:
- `~/.claude/skills/<skill-name>/SKILL.md` (global)
- `.claude/skills/<skill-name>/SKILL.md` (project)

### Step V2: Run Validator

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate-skill.py --grade {path}/SKILL.md
```

### Step V3: Review Grade

100-point rubric across 5 pillars:

| Pillar | Max | What It Measures |
|--------|-----|------------------|
| Progressive Disclosure | 30 | Token economy, layered structure, navigation |
| Ease of Use | 25 | Metadata, discoverability, workflow clarity |
| Utility | 20 | Problem solving, examples, feedback loops |
| Spec Compliance | 15 | Frontmatter, naming, description quality |
| Writing Style | 10 | Voice, objectivity, conciseness |
| Modifiers | +/-5 | Bonuses/penalties for patterns |

Grade scale: A (90+), B (80-89), C (70-79), D (60-69), F (<60)

See `${CLAUDE_SKILL_DIR}/references/validation-rules.md` for detailed sub-criteria.

### Step V4: Report Results

Present the grade report with specific fix recommendations. Prioritize fixes by point value (highest first).

### Step V5: Auto-Fix (if requested)

If the user says "fix it" or "auto-fix", apply the suggested improvements:
1. Add missing sections (Overview, Prerequisites, Output)
2. Add "Use when" / "Trigger with" to description
3. Move author/version from metadata to top-level
4. Fix path variables to `${CLAUDE_SKILL_DIR}/`
5. Re-run grading to confirm improvement

## Examples

### Simple Skill (Create Mode)

```
User: Create a skill called "code-review" that reviews code quality

Creates:
~/.claude/skills/code-review/
├── SKILL.md
└── evals/
    └── evals.json

Frontmatter:
---
name: code-review
description: |
  Make sure to use this skill whenever reviewing code for quality, security
  vulnerabilities, and best practices. Use when doing code reviews, PR analysis,
  or checking code quality. Trigger with "/code-review" or "review this code".
allowed-tools: "Read,Glob,Grep"
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
model: inherit
---
```

### Full Package with Arguments (Create Mode)

```
User: Create a skill that generates release notes from git history

Creates:
~/.claude/skills/generating-release-notes/
├── SKILL.md              (argument-hint: "[version-tag]")
├── scripts/
│   └── parse-commits.py
├── references/
│   └── commit-conventions.md
├── templates/
│   └── release-template.md
└── evals/
    └── evals.json

Uses $ARGUMENTS[0] for version tag.
Uses context: fork for isolated execution.
```

### Validate Mode

```
User: Grade my skill at ~/.claude/skills/code-review/SKILL.md

Runs: python3 ${CLAUDE_SKILL_DIR}/scripts/validate-skill.py --grade ~/.claude/skills/code-review/SKILL.md

Output:
  Grade: B (84/100)
  Improvements:
    - Add "Trigger with" to description (+3 pts)
    - Add ## Output section (+2 pts)
    - Add ## Prerequisites section (+2 pts)
```

## Edge Cases

- **Name conflicts**: Check if skill directory already exists before creating
- **Empty arguments**: If skill uses `$ARGUMENTS`, handle the empty case
- **Long content**: If SKILL.md exceeds 300 lines during writing, stop and split to references
- **Bash scoping**: If user requests raw `Bash`, always scope it
- **Model selection**: Default to `inherit`, only override with good reason
- **Undertriggering**: If skill isn't activating, make description more aggressive/pushy
- **Legacy metadata nesting**: If found, move author/version/license to top-level

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Name exists | Directory already present | Choose different name or confirm overwrite |
| Invalid name | Not kebab-case or >64 chars | Fix to lowercase-with-hyphens |
| Validation fails | Missing fields or anti-patterns | Run validator, fix reported issues |
| Resource missing | `${CLAUDE_SKILL_DIR}/` ref points to nonexistent file | Create the file or fix the reference |
| Undertriggering | Description too passive | Add "Make sure to use whenever..." phrasing |
| Eval failures | Skill not producing expected output | Iterate on instructions and re-test |
| Low grade | Missing scored sections or fields | Add Overview, Prerequisites, Output sections |

## Resources

**References:** `${CLAUDE_SKILL_DIR}/references/`
- `source-of-truth.md` — Canonical spec | `frontmatter-spec.md` — Field reference | `validation-rules.md` — 100-point rubric
- `workflows.md` — Workflow patterns | `output-patterns.md` — Output formats | `schemas.md` — JSON schemas (evals, grading, benchmarks)
- `anthropic-comparison.md` — Gap analysis | `advanced-eval-workflow.md` — Eval, iteration, optimization, platform notes

**Agents** (read when spawning subagents): `${CLAUDE_SKILL_DIR}/agents/`
- `grader.md` — Assertion evaluation | `comparator.md` — Blind A/B comparison | `analyzer.md` — Benchmark analysis

**Scripts:** `${CLAUDE_SKILL_DIR}/scripts/`
- `validate-skill.py` — 100-point rubric grading | `quick_validate.py` — Lightweight validation
- `aggregate_benchmark.py` — Benchmark stats | `run_eval.py` — Trigger accuracy testing
- `run_loop.py` — Description optimization loop | `improve_description.py` — LLM-powered rewriting
- `generate_report.py` — HTML reports | `package_skill.py` — .skill packaging | `utils.py` — Shared utilities

**Eval Viewer:** `${CLAUDE_SKILL_DIR}/eval-viewer/` — `generate_review.py` + `viewer.html` (interactive output comparison)
**Assets:** `${CLAUDE_SKILL_DIR}/assets/eval_review.html` (trigger eval set editor)
**Templates:** `${CLAUDE_SKILL_DIR}/templates/skill-template.md` (SKILL.md skeleton)

---

## Running and Evaluating Test Cases

For detailed empirical eval workflow (Steps E1-E5), read `${CLAUDE_SKILL_DIR}/references/advanced-eval-workflow.md`.

**Quick summary:** Spawn with-skill and baseline subagents in parallel -> draft assertions while running -> capture timing data from task notifications -> grade with `${CLAUDE_SKILL_DIR}/agents/grader.md` -> aggregate with `scripts/aggregate_benchmark.py` -> launch `eval-viewer/generate_review.py` for interactive human review -> read `feedback.json`.

---

## Improving the Skill

For iteration loop details, read `${CLAUDE_SKILL_DIR}/references/advanced-eval-workflow.md` (section "Improving the Skill").

**Key principles:** Generalize from feedback (don't overfit), keep prompts lean, explain the *why* behind rules (not just prescriptions), and bundle repeated helper scripts.

---

## Description Optimization (Automated)

For the full pipeline (Steps D1-D4), read `${CLAUDE_SKILL_DIR}/references/advanced-eval-workflow.md` (section "Description Optimization"). Quick summary: generate 20 realistic trigger eval queries -> review with user via `${CLAUDE_SKILL_DIR}/assets/eval_review.html` -> run `python -m scripts.run_loop` (60/40 train/test, 3 runs/query, up to 5 iterations) -> apply `best_description`.

## Advanced: Blind Comparison

For A/B testing between skill versions, read `${CLAUDE_SKILL_DIR}/agents/comparator.md` and `${CLAUDE_SKILL_DIR}/agents/analyzer.md`. Optional; most users won't need it.

## Packaging

`python -m scripts.package_skill <path/to/skill-folder> [output-directory]` — Creates distributable `.skill` zip after validation.

## Platform-Specific Notes

See `${CLAUDE_SKILL_DIR}/references/advanced-eval-workflow.md` (section "Platform-Specific Notes").
- **Claude.ai**: No subagents — run tests yourself, skip benchmarking/description optimization.
- **Cowork**: Full subagent workflow. Use `--static` for eval viewer. Generate viewer BEFORE self-evaluation.
