---
description: Discover skill candidates from repeating session patterns
allowed-tools: Read, Write, Bash, Glob, Grep, AskUserQuestion, TodoWrite
---

## Arguments
- `--days N`: Analyze sessions from last N days (default: 14)
- `--project <path>`: Analyze sessions from a specific project (default: current project)
- `--all-projects`: Analyze ALL projects (slower, use when looking for cross-project patterns)
- `--dry-run`: Show analysis without generating skill files

## Context
- Current project: !`pwd`
- Session files location: `~/.claude/projects/`
- Skills location: `.claude/commands/` (per-project) or `~/.claude/commands/` (global)

## Your Task

You are analyzing session history to discover **repeating patterns** that could become reusable skills.

### IMPORTANT: AI-Powered Detection

**DO NOT use hardcoded patterns, regex, or keyword matching.**

Your job is to **reason** about the sessions and identify:
1. **Workflow patterns** - Multi-step sequences the user requests repeatedly
2. **Misunderstanding patterns** - Corrections that keep happening (could become skill guardrails)
3. **Prompt sequences** - Similar intents expressed in different words

Use your semantic understanding. The same intent might appear as:
- "search for X on linkedin"
- "find X's linkedin profile"
- "lookup X on linkedin"

These are the **same pattern** despite different wording.

---

## Workflow

### Step 1: Initialize Task Tracking

**REQUIRED:** Use TodoWrite immediately to show progress. Update after each step.

```json
{
  "todos": [
    {"content": "Parse arguments", "status": "in_progress", "activeForm": "Parsing command arguments"},
    {"content": "Gather session data", "status": "pending", "activeForm": "Reading session files"},
    {"content": "Check existing commands", "status": "pending", "activeForm": "Checking existing commands"},
    {"content": "Analyze for patterns", "status": "pending", "activeForm": "Analyzing sessions for patterns"},
    {"content": "Propose skill candidates", "status": "pending", "activeForm": "Proposing skill candidates"},
    {"content": "Assign skills to projects", "status": "pending", "activeForm": "Assigning skills to projects"},
    {"content": "Get user approval", "status": "pending", "activeForm": "Getting user approval"},
    {"content": "Generate skill files", "status": "pending", "activeForm": "Generating skill files"},
    {"content": "Validate skills", "status": "pending", "activeForm": "Validating generated skills"}
  ]
}
```

### Step 2: Parse Arguments

Check for:
- `--days N` → Limit to last N days of sessions (default: 14)
- `--project <path>` → Specific project path
- `--all-projects` → Scan all projects (otherwise default to current project)
- `--dry-run` → Analysis only, no file generation

**Default behavior:** Only scan current project unless `--all-projects` is specified.

### Step 3: Gather Session Data

**Default behavior:** Only scan current project's sessions unless `--all-projects` specified.

```bash
# Get current project's session directory
PROJECT_PATH=$(pwd)
PROJECT_DIR=$(echo "$PROJECT_PATH" | sed 's|/|-|g' | sed 's|^-||')
SESSION_PATH="$HOME/.claude/projects/-${PROJECT_DIR}/"

# Verify session directory exists
ls -la "$SESSION_PATH" 2>/dev/null | head -5
```

If `--all-projects` is specified:
```bash
# Find all project session directories
ls -la ~/.claude/projects/ 2>/dev/null | head -20
```

Find session files:
```bash
# Find recent sessions (adjust date filter based on --days)
find "$SESSION_PATH" -name "*.jsonl" -mtime -14 -type f 2>/dev/null
```

**Extract user messages using the existing script:**

```bash
# Use the plugin's extraction script - DO NOT reinvent with bash/jq
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/extract_session_learnings.py" "$SESSION_FILE"
```

The extraction script handles:
- String and list content formats
- isMeta filtering (excludes command expansions)
- Skip patterns (XML, JSON, tool results)

**What to extract:**
- User prompts (natural language requests)
- Sequences of tool calls that followed
- Any corrections or clarifications

### Step 3b: Check Existing Commands

Before analyzing patterns, discover what skills already exist:

```bash
# Check current project
ls .claude/commands/*.md 2>/dev/null | xargs -I{} basename {} .md

# Check global commands
ls ~/.claude/commands/*.md 2>/dev/null | xargs -I{} basename {} .md
```

Store the list of existing command names. During pattern analysis (Step 4), if a pattern's suggested name matches an existing command:
- **Skip it** from the NEW candidates list
- Show it in "Existing skills (patterns match)" section

This prevents proposing duplicates.

### Step 4: Analyze for Patterns (AI-Powered)

**This is the core step. Use your reasoning to identify patterns.**

Read the extracted session data and think:

1. **Workflow Repetition**
   - "I see the user asked for [X] multiple times"
   - "Each time, I performed steps: A → B → C"
   - "This could be automated as a skill"

2. **Semantic Similarity**
   - "These 3 requests have different wording but same intent"
   - "User wants to [accomplish Y] but phrases it differently"
   - "A skill with good trigger detection would help"

3. **Correction Patterns**
   - "User corrected me twice about [Z]"
   - "This should be a guardrail in the skill"
   - "Next time, the skill should do [Z] by default"

**Output your analysis GROUPED BY PROJECT:**

```
═══ PROJECT: edu-website ═══

PATTERN 1: Campaign Analytics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Evidence (all from edu-website):
- Session [date]: "review analytics for..."
- Session [date]: "check campaign performance..."

Intent: [What the user is trying to accomplish]

Typical Steps:
1. [First action]
2. [Second action]
3. [Third action]

Corrections Applied: [Any guardrails learned from corrections]

Suggested Skill Name: /campaign-analytics
Confidence: High
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

═══ PROJECT: bayram-os ═══

PATTERN 2: Daily Review
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Evidence (all from bayram-os):
- Session [date]: "review my productivity..."
...
```

### Step 5: Propose Skill Candidates

Present discovered patterns to the user:

```
════════════════════════════════════════════════════════════
SKILL CANDIDATES DISCOVERED
════════════════════════════════════════════════════════════

Existing skills (patterns match existing commands):
- /campaign-analytics (already in .claude/commands/)
- /zettel-update (already in .claude/commands/)

NEW skill candidates from analyzing [M] sessions:

1. /[skill-name] (Confidence: High) — from [project-name]
   → [One-line description]
   Evidence: [N] similar requests found

2. /[skill-name] (Confidence: Medium) — from [project-name]
   → [One-line description]
   Evidence: [N] similar requests found

════════════════════════════════════════════════════════════
```

**Note:** If all discovered patterns match existing commands, inform the user:
> "All discovered patterns already have corresponding skills. No new skills to propose."

Use AskUserQuestion to get feedback:
- Which patterns should become skills?
- Any patterns to skip?
- Any name changes?

### Step 5b: Assign Skills to Projects

For each approved skill, determine the correct project location.

**Project Detection Logic:**
- If ALL evidence comes from one project → suggest that project
- If evidence spans multiple projects → ask user
- If pattern is general-purpose → suggest global (`~/.claude/commands/`)

Present assignment table:
```
┌──────────────────────┬─────────────────────┬──────────────────────────────┐
│        Skill         │  Suggested Project  │            Reason            │
├──────────────────────┼─────────────────────┼──────────────────────────────┤
│ /daily-review        │ bayram-os           │ All evidence from bayram-os  │
│ /campaign-analytics  │ edu-website         │ All evidence from edu-website│
│ /draft-outreach      │ Global              │ Used across multiple projects│
└──────────────────────┴─────────────────────┴──────────────────────────────┘
```

Use AskUserQuestion to confirm or adjust assignments.

### Step 6: Generate Skill Files

**Pre-flight checks:**
```bash
# Ensure .claude/commands exists for each target project
for project in [list of target projects]; do
  mkdir -p "$project/.claude/commands"
done
```

For each approved skill candidate, generate a skill file in `.claude/commands/`:

**Skill File Template:**
```markdown
---
description: [One-line description]
allowed-tools: [Relevant tools based on workflow]
---

## Context
[Any context the skill needs]

## Your Task

[Clear description of what the skill does]

### Steps

1. [First step]
2. [Second step]
3. [Third step]

### Guardrails
[Any learned corrections/constraints]

---
*Generated by /reflect-skills from [N] session patterns*
```

Write to: `[project-path]/.claude/commands/[skill-name].md`

For global skills: `~/.claude/commands/[skill-name].md`

### Step 6b: Validate Skills

After generating each skill file, verify it works:

1. **File exists:**
   ```bash
   ls -la [project-path]/.claude/commands/[skill-name].md
   ```

2. **Has valid frontmatter:**
   ```bash
   head -5 [project-path]/.claude/commands/[skill-name].md
   ```

3. **Inform user:**
   > "Skill file created. Restart Claude Code session or start new conversation to see /[skill-name] in autocomplete."

### Step 7: Summary

```
════════════════════════════════════════════════════════════
SKILL GENERATION COMPLETE
════════════════════════════════════════════════════════════

Created [N] new skill(s):

Project: bayram-os
  - /daily-review: .claude/commands/daily-review.md

Project: edu-website
  - /campaign-analytics: .claude/commands/campaign-analytics.md

Global:
  - /draft-outreach: ~/.claude/commands/draft-outreach.md

Next steps:
1. Restart Claude Code or start new conversation
2. Test with: /[skill-name]
3. Iterate on skill content as needed

════════════════════════════════════════════════════════════
```

---

## Key Principles

1. **Semantic over Syntactic** - Match intent, not keywords
2. **Evidence-Based** - Show the user WHY you think it's a pattern
3. **Human-in-the-Loop** - User approves before generation
4. **Minimal but Useful** - Only propose skills that would genuinely save time
5. **Learn from Corrections** - Build guardrails from past mistakes
6. **Right Location** - Skills go to `.claude/commands/` in the correct project

---

## Example Analysis

Given these session excerpts:

```
Session 1: "find john smith on linkedin and get his email"
Session 2: "linkedin lookup for sarah jones, need her contact info"
Session 3: "search linkedin for the CTO of acme corp"
```

Your analysis should reason:

> "I see 3 requests that are semantically similar - all are about finding
> someone on LinkedIn. The specific names and details vary, but the workflow
> is consistent: search LinkedIn → find profile → extract contact info.
> This is a strong candidate for a /linkedin-lookup skill."

NOT:

> "I found 3 messages containing 'linkedin' - potential skill."

The first is semantic reasoning. The second is keyword matching.
