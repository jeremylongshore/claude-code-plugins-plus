---
description: Reflect on session corrections and update CLAUDE.md (with human review)
allowed-tools: Read, Edit, Write, Glob, Bash, Grep, AskUserQuestion, TodoWrite
---

## Arguments
- `--dry-run`: Preview all changes without prompting or writing.
- `--scan-history`: Scan ALL past sessions for corrections (useful for first-time setup or cold start).
- `--days N`: Limit history scan to last N days (default: 30). Only used with `--scan-history`.
- `--targets`: Show detected AI assistant config files and exit.
- `--review`: Show learnings with stale/decayed entries for review.
- `--dedupe`: Scan CLAUDE.md for similar entries and propose consolidations.
- `--organize`: Analyze memory hierarchy and suggest reorganization across tiers.
- `--include-tool-errors`: Include project-specific tool execution errors in scan (auto-enabled with `--scan-history`).
- `--model MODEL`: Model for semantic analysis (default: `sonnet`). Use `haiku` for faster/cheaper runs or `opus` for maximum accuracy.

## Context
- Project CLAUDE.md: @CLAUDE.md
- Global CLAUDE.md: @~/.claude/CLAUDE.md
- Learnings queue (per-project): !`python3 "$(dirname "$(dirname "$(readlink -f "$0")")")/scripts/read_queue.py" 2>/dev/null || echo "[]"`
- Current project: !`pwd`

## Multi-Target Export

Claude-reflect syncs learnings to CLAUDE.md files (including subdirectories), skill files, and AGENTS.md.

**Supported Targets:**

| Target | File Path | Format | Notes |
|--------|-----------|--------|-------|
| **Global CLAUDE.md** | `~/.claude/CLAUDE.md` | Markdown | Always enabled |
| **Project CLAUDE.md** | `./CLAUDE.md` | Markdown | If exists |
| **CLAUDE.local.md** | `./CLAUDE.local.md` | Markdown | Personal, gitignored |
| **Subdirectory CLAUDE.md** | `./**/CLAUDE.md` | Markdown | Auto-discovered |
| **Project Rules** | `./.claude/rules/*.md` | Markdown | Modular rules, optional path-scoping |
| **User Rules** | `~/.claude/rules/*.md` | Markdown | Global modular rules |
| **Skill Files** | `./commands/*.md` | Markdown | When correction relates to skill |
| **Auto Memory** | `~/.claude/projects/<project>/memory/*.md` | Markdown | Low-confidence, exploratory learnings |
| **AGENTS.md** | `./AGENTS.md` | Markdown | Industry standard (Codex, Cursor, Aider, Jules, Zed, Factory) |

**Target Discovery:**

Use the Python utility to find all memory tier files:
```python
from scripts.lib.reflect_utils import find_claude_files
files = find_claude_files()
# Returns list of {path, relative_path, type, frontmatter}
# Types: 'global', 'root', 'local', 'subdirectory', 'rule', 'user-rule'
```

Or discover manually:
```bash
# Find all CLAUDE.md files (excluding node_modules, .git, venv, etc.)
find . -name "CLAUDE.md" -type f \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  -not -path "*/venv/*" \
  -not -path "*/.venv/*"
# Also check rule files and local
ls .claude/rules/*.md 2>/dev/null
ls CLAUDE.local.md 2>/dev/null
ls ~/.claude/rules/*.md 2>/dev/null
```

**Target Selection (Hierarchy-Aware Routing):**
- **Guardrail corrections** ("don't do X") → `.claude/rules/guardrails.md`
- **Model preferences** → existing model-preferences rule file or `~/.claude/CLAUDE.md`
- **Global behavioral** (always/never/prefer) → `~/.claude/CLAUDE.md`
- **Path-scoped** (learning mentions directory covered by rule's `paths:`) → that rule file
- **Personal/local** (machine-specific, not for team) → `./CLAUDE.local.md`
- **Low-confidence** (0.60-0.74) → auto memory for later promotion
- **Project-specific** → `./CLAUDE.md` or subdirectory file
- Let users override routing with AI reasoning

**Note on Confidence & Decay:**
- Confidence scores help prioritize learnings during `/reflect` review
- Decay applies to **queue items only** — if a learning sits unprocessed for too long, it's flagged as stale
- Once applied to CLAUDE.md, entries are permanent (edit manually to remove)

## Your Task

### MANDATORY: Initialize Task Tracking (Step 0)

**BEFORE starting any work**, use TodoWrite to create a task list for the entire workflow. This ensures no steps are skipped and provides visibility into progress.

**Why this is critical:**
- The /reflect workflow has 10+ phases that must execute in order
- Without tracking, Claude may skip steps or lose context
- TodoWrite acts as a checkpoint system ensuring completeness

**Initialize with this task list (adjust based on arguments):**

```
TodoWrite tasks for /reflect:
1. "Parse arguments and check flags" (--dry-run, --scan-history, etc.)
2. "Load learnings queue from ~/.claude/learnings-queue.json"
3. "Scan historical sessions" (if --scan-history)
4. "Validate learnings with semantic analysis"
5. "Filter by project context (global vs project-specific)"
6. "Deduplicate similar learnings"
7. "Check for duplicates in existing CLAUDE.md"
8. "Present summary and get user decision"
9. "Apply changes to CLAUDE.md/AGENTS.md"
10. "Clear queue and confirm completion"
```

**Workflow rules:**
- **Mark in_progress BEFORE starting each step** - this signals what's happening
- **Mark completed IMMEDIATELY after finishing** - don't batch updates
- **Only ONE task should be in_progress at a time**
- **Never skip a step** - if a step doesn't apply, mark it completed with a note
- **If blocked or error occurs**, keep task as in_progress and create a new task for the blocker

**Example TodoWrite call at start:**
```json
{
  "todos": [
    {"content": "Parse arguments (--scan-history detected)", "status": "in_progress", "activeForm": "Parsing command arguments"},
    {"content": "Load learnings queue", "status": "pending", "activeForm": "Loading queue from ~/.claude/learnings-queue.json"},
    {"content": "Scan historical sessions", "status": "pending", "activeForm": "Scanning past sessions for corrections"},
    {"content": "Validate with semantic analysis", "status": "pending", "activeForm": "Validating learnings semantically"},
    {"content": "Filter by project context", "status": "pending", "activeForm": "Filtering global vs project learnings"},
    {"content": "Deduplicate similar learnings", "status": "pending", "activeForm": "Removing duplicate learnings"},
    {"content": "Check existing CLAUDE.md for duplicates", "status": "pending", "activeForm": "Checking for existing entries"},
    {"content": "Present summary to user", "status": "pending", "activeForm": "Presenting learnings summary"},
    {"content": "Apply changes to target files", "status": "pending", "activeForm": "Writing to CLAUDE.md/AGENTS.md"},
    {"content": "Clear queue and confirm", "status": "pending", "activeForm": "Finalizing and clearing queue"}
  ]
}
```

**DO NOT PROCEED** to the next section until you have initialized the task list with TodoWrite.

---

### Handle --targets Argument

**If user passed `--targets`:**

Detect and display all AI assistant config files with **line counts** and **size warnings**.

**Line Count Threshold:** 150 lines (research suggests frontier models handle ~150-200 instructions reliably)

**Detection Steps:**

1. Find all memory tier files using `find_claude_files()` (discovers CLAUDE.md, CLAUDE.local.md, rule files)
2. Count lines in each file
3. Check for auto memory directory
4. Display with status indicator:
   - `✓` = under 150 lines (healthy)
   - `⚠️` = over 150 lines (consider cleanup)

```python
# Cross-platform line counting (works on Windows, macOS, Linux)
from pathlib import Path

def count_lines(filepath):
    try:
        return len(Path(filepath).expanduser().read_text().splitlines())
    except:
        return 0

# Example usage
count_lines("~/.claude/CLAUDE.md")
count_lines("./CLAUDE.md")
```

**Display format:**
```
════════════════════════════════════════════════════════════
MEMORY HIERARCHY — TARGET FILES
════════════════════════════════════════════════════════════

CLAUDE.md Files:
  ~/.claude/CLAUDE.md (global)           42 lines  ✓
  ./CLAUDE.md (project)                 156 lines  ⚠️
  ./CLAUDE.local.md (personal)           12 lines  ✓
  ./src/CLAUDE.md (subdirectory)         28 lines  ✓

Rule Files:
  ./.claude/rules/guardrails.md          8 lines  ✓
  ./.claude/rules/coding-style.md       15 lines  ✓  [paths: src/]
  ~/.claude/rules/model-preferences.md  10 lines  ✓

Auto Memory:
  ~/.claude/projects/.../memory/         3 files (general.md, tool-usage.md, workflow.md)

Other:
  AGENTS.md                              ✗ not found

────────────────────────────────────────────────────────────
⚠️  ./CLAUDE.md exceeds 150 lines
    Tip: Run /reflect --dedupe to consolidate similar entries
    Tip: Run /reflect --organize to redistribute entries across tiers
────────────────────────────────────────────────────────────

To create new targets:
  touch AGENTS.md                    # Enable AGENTS.md sync
  touch CLAUDE.local.md              # Personal learnings (gitignored)
  mkdir -p .claude/rules             # Enable modular rule files

════════════════════════════════════════════════════════════
```

**Logic:**
- Show warning section only if ANY file exceeds 150 lines
- List all files over threshold in the warning
- Always suggest `--dedupe` and `--organize` as remediation
- Show path-scoping info for rule files with `paths:` frontmatter

Exit after showing targets (don't process learnings).

### Handle --review Argument

**If user passed `--review`:**

Show learnings with their confidence and decay status:

```bash
cat ~/.claude/learnings-queue.json | jq -r '.[] | "\(.timestamp) | conf:\(.confidence // 0.5) | decay:\(.decay_days // 90)d | \(.message | .[0:60])"'
```

Display table of learnings with decay status:
```
═══════════════════════════════════════════════════════════
LEARNINGS REVIEW — Confidence & Decay Status
═══════════════════════════════════════════════════════════

┌────┬──────────┬────────┬────────────────────────────────┐
│ #  │ Conf.    │ Decay  │ Learning                       │
├────┼──────────┼────────┼────────────────────────────────┤
│ 1  │ 0.90 ✓   │ 120d   │ Use gpt-5.1 for reasoning     │
│ 2  │ 0.60     │ 60d ⚠  │ Enable flag X for API calls   │
│ 3  │ 0.40 ⚠   │ 30d ⚠  │ Consider using batch mode     │
└────┴──────────┴────────┴────────────────────────────────┘

Legend: ✓ High confidence  ⚠ Low confidence/Near decay
═══════════════════════════════════════════════════════════
```

Exit after showing review (don't process learnings).

### Handle --dedupe Argument

**If user passed `--dedupe`:**

Scan existing CLAUDE.md files for similar entries AND contradictions.

**1. Read both CLAUDE.md files:**
```bash
cat ~/.claude/CLAUDE.md
cat CLAUDE.md 2>/dev/null
```

**2. Extract all bullet points:**
Look for lines starting with `- ` under section headers. Track line numbers.

**3. Detect contradictions using semantic analysis:**

Use the contradiction detector to find conflicting entries:
```python
from lib.semantic_detector import detect_contradictions

# Collect all entries from both files
entries = [...]  # List of bullet point strings

contradictions = detect_contradictions(entries)
# Returns: [{"entry1": "...", "entry2": "...", "conflict": "reason"}]
```

**4. Analyze for semantic similarity:**
Group entries that:
- Reference the same tool/model/concept
- Give overlapping or redundant advice
- Could be merged without losing information

**5. Present findings:**

```
═══════════════════════════════════════════════════════════
CLAUDE.MD DEDUPLICATION SCAN
═══════════════════════════════════════════════════════════

⚠️ CONTRADICTIONS FOUND (2)
────────────────────────────────────────────────────────────

#1: Conflicting indentation preferences
    Line 12: "- Use tabs for indentation"
    Line 78: "- Use spaces for indentation"
    Conflict: opposite indentation preferences

#2: Conflicting model recommendations
    Line 24: "- Use gpt-5.1 for all tasks"
    Line 89: "- Prefer Claude for reasoning tasks"
    Conflict: different model preferences for similar tasks

────────────────────────────────────────────────────────────

SIMILAR ENTRIES (2 groups)
────────────────────────────────────────────────────────────

Group 1 (Global CLAUDE.md):
  Line 45: "- Use gpt-5.1 for complex tasks"
  Line 52: "- Prefer gpt-5.1 for reasoning"
  → Proposed: "- Use gpt-5.1 for complex reasoning tasks"

Group 2 (Project CLAUDE.md):
  Line 12: "- Always use venv"
  Line 28: "- Create virtual environment for Python"
  → Proposed: "- Use venv for Python projects"

────────────────────────────────────────────────────────────
Unique entries: 23 (no changes needed)
═══════════════════════════════════════════════════════════
```

**6. Handle contradictions with AskUserQuestion:**

For each contradiction found:
```json
{
  "questions": [{
    "question": "Contradiction #1: 'Use tabs' vs 'Use spaces' - How to resolve?",
    "header": "Conflict",
    "multiSelect": false,
    "options": [
      {"label": "Keep first", "description": "Keep 'Use tabs for indentation' (line 12)"},
      {"label": "Keep second", "description": "Keep 'Use spaces for indentation' (line 78)"},
      {"label": "Merge", "description": "Create a combined entry that resolves the conflict"},
      {"label": "Keep both", "description": "Leave both entries (they may apply to different contexts)"}
    ]
  }]
}
```

**7. Handle similarity groups with AskUserQuestion:**
```json
{
  "questions": [{
    "question": "Apply deduplication to CLAUDE.md files?",
    "header": "Dedupe",
    "multiSelect": false,
    "options": [
      {"label": "Apply all consolidations", "description": "Merge 2 groups, remove 4 redundant lines"},
      {"label": "Review each group", "description": "Decide per group"},
      {"label": "Cancel", "description": "Keep files unchanged"}
    ]
  }]
}
```

**8. Apply changes:**
- Use Edit tool to resolve contradictions based on user choices
- Replace redundant entries with consolidated versions
- Remove duplicate lines
- Preserve section structure

Exit after deduplication (don't process queue).

### Handle --organize Argument

**If user passed `--organize`:**

Analyze the full memory hierarchy and suggest reorganization to reduce clutter and improve routing.

**1. Inventory all memory locations:**

```python
from scripts.lib.reflect_utils import find_claude_files, read_auto_memory, read_all_memory_entries

files = find_claude_files()
auto_memory = read_auto_memory()
all_entries = read_all_memory_entries()
```

Count lines, entries, and files for each tier.

**2. Detect issues:**

| Issue | Detection | Fix |
|-------|-----------|-----|
| Overgrown file (>150 lines) | Line count check | Split into rule files or subdirectory CLAUDE.md |
| Wrong-tier entries | Global-looking entries in project file or vice versa | Move to correct tier |
| Scattered topics | Same topic (e.g., model preferences) across multiple files | Consolidate into rule file |
| Path-scoping opportunities | Entries mentioning specific directories | Create path-scoped rule files |
| Auto memory promotion candidates | Confirmed patterns in auto memory | Promote to CLAUDE.md |
| Cross-tier duplicates | Same entry in multiple tiers | Remove duplicates |

**3. Present findings:**

```
════════════════════════════════════════════════════════════
MEMORY HIERARCHY ANALYSIS
════════════════════════════════════════════════════════════

Current state:
  ~/.claude/CLAUDE.md          182 lines  ⚠️ (over 150)
  ./CLAUDE.md                   95 lines  ✓
  .claude/rules/                 0 files
  Auto memory                    2 files

Issues found: 4
────────────────────────────────────────────────────────────

#1 OVERGROWN: ~/.claude/CLAUDE.md (182 lines)
   → Suggestion: Extract model preferences to ~/.claude/rules/model-preferences.md
   → Suggestion: Extract guardrails to .claude/rules/guardrails.md

#2 WRONG TIER: 3 global-looking entries in ./CLAUDE.md
   → "Always use venv" — should be in ~/.claude/CLAUDE.md
   → "Never use force push" — should be in ~/.claude/CLAUDE.md

#3 PROMOTION: 2 auto memory entries confirmed across sessions
   → "Use batch mode for API calls" — promote to ./CLAUDE.md

#4 DUPLICATE: 1 entry found in multiple tiers
   → "Use gpt-5.1 for reasoning" in both ~/.claude/CLAUDE.md and auto memory

════════════════════════════════════════════════════════════
```

**4. Get user approval per fix:**

Use AskUserQuestion for each proposed reorganization:
```json
{
  "questions": [{
    "question": "Apply reorganization #1: Extract model preferences to rule file?",
    "header": "Organize",
    "multiSelect": false,
    "options": [
      {"label": "Yes, extract (Recommended)", "description": "Move 12 model entries to ~/.claude/rules/model-preferences.md"},
      {"label": "Skip", "description": "Leave entries in current location"}
    ]
  }]
}
```

**5. Apply reorganization:**
- Use Edit tool to move content between files
- Create new rule files as needed
- Remove duplicates from source files
- Preserve section structure in all files

**6. Exit after reorganization (don't process queue).**

### First-Run Detection (Per-Project)

Check if /reflect has been run in THIS project before. Run these commands separately:

**WARNING**: Do NOT combine these into a single compound command with `$(...)`. Claude Code's bash executor mangles subshell syntax. Run each command individually and manually substitute the result.

1. Find the project folder name:
```bash
ls ~/.claude/projects/ | grep -i "$(basename "$(pwd)")"
```

2. Check if initialized (replace PROJECT_FOLDER with result from step 1):
```bash
test -f ~/.claude/projects/PROJECT_FOLDER/.reflect-initialized && echo "initialized" || echo "first-run"
```

**If "first-run" for this project AND user did NOT pass `--scan-history`:**

Use AskUserQuestion to recommend historical scan:
```json
{
  "questions": [{
    "question": "First time running /reflect in this project. Scan past sessions for learnings?",
    "header": "First run",
    "multiSelect": false,
    "options": [
      {"label": "Yes, scan history (Recommended)", "description": "Find corrections from past sessions in this project"},
      {"label": "No, just process queue", "description": "Only process learnings captured by hooks"}
    ]
  }]
}
```

If user chooses "Yes, scan history", proceed as if `--scan-history` was passed.

### Step 0: Check Arguments

**If user passed `--dry-run`:**
- Process all learnings with project filtering
- Show proposed changes with line numbers
- Do NOT prompt for actions, do NOT write
- End with: "Dry run complete. Run /reflect without --dry-run to apply."

**If user passed `--scan-history`:**
- FIRST: Load the queue (Step 1) - queued items are NEVER skipped
- THEN: Scan ALL historical sessions for this project (Step 0.5)
- Combine queue items + history scan results into working list
- Proceed to Step 3 (Project-Aware Filtering)

### Step 0.5: Historical Scan (only with --scan-history)

Scan past sessions for corrections missed by hooks. Useful for:
- First-time /reflect installation (cold start)
- Periodic deep review of past learnings

**0.5a. Find ALL session files for this project:**

1. First, list project folders to find the correct path pattern:
   ```bash
   ls ~/.claude/projects/ | grep -i "$(basename $(pwd))"
   ```

2. **Handle underscores vs hyphens:** Directory names may use underscores (`darwin_new`) but encoded paths use hyphens (`darwin-new`). If first grep fails, try replacing underscores:
   ```bash
   # If no match, try with hyphens instead of underscores
   ls ~/.claude/projects/ | grep -i "$(basename $(pwd) | tr '_' '-')"
   ```

3. Then list ALL session files in that folder:
   ```bash
   ls ~/.claude/projects/[PROJECT_FOLDER]/*.jsonl
   ```

Note: Project paths have `/` replaced with `-`. For `/Users/bob/code/myapp`, look for `-Users-bob-code-myapp`.

**IMPORTANT**: With `--scan-history`, process ALL session files (not just recent ones). This includes:
- Main session files (UUID format like `fa5ae539-d170-4fa8-a8d2-bf50b3ec2861.jsonl`)
- Agent files (`agent-*.jsonl`) - these may contain corrections too
- Apply `--days N` filter by checking file modification times if specified

**0.5b. Extract corrections from session files:**

Session files are JSONL. Use jq to extract user messages, then grep for patterns.

**CRITICAL**: Filter out command expansion messages using `isMeta != true`. Command expansions (like /reflect itself) are stored with `isMeta: true` and contain documentation text that would cause false positives.

**DYNAMIC PATTERN SELECTION**: Before running grep, sample a few user messages to detect the conversation language. If non-English, adapt the patterns accordingly:

| Language | Example patterns to add |
|----------|------------------------|
| Russian | `нет,? используй\|не используй\|на самом деле\|запомни:\|лучше\|предпочитаю` |
| Spanish | `no,? usa\|no uses\|en realidad\|recuerda:\|prefiero\|siempre usa` |
| German | `nein,? verwende\|nicht verwenden\|eigentlich\|merke:\|bevorzuge\|immer` |

Generate appropriate patterns for the detected language and combine with English patterns.

**Default English patterns:** `remember:`, `no, use`, `don't use`, `actually`, `stop using`, `never use`, `that's wrong`, `I meant`, `use X not Y`

For each `.jsonl` file in the project folder, extract user messages that match correction patterns. Use your judgment on the best extraction method - you can use Read, Grep, Bash with jq, or any combination that works.

**What to extract:**
1. **User messages** with correction patterns (from `type: "user"` entries with `isMeta != true`)
2. **Tool rejections** - look for `toolUseResult` fields containing "user said:" followed by feedback text
   - "user said:" followed by empty content means rejection without feedback - skip these

**Key file structure:**
- Session files: `~/.claude/projects/[PROJECT_FOLDER]/*.jsonl`
- User messages: `{"type": "user", "message": {"content": [{"type": "text", "text": "..."}]}}`
- Tool rejections: `{"toolUseResult": "The user doesn't want to proceed\nuser said:\n[feedback]"}`

**0.5b-extra. Tool rejections are HIGH confidence:**

When a user stops a tool and provides feedback, this is a strong correction signal. The feedback appears after "user said:" (may be on the next line in the JSON).

**CRITICAL: Tool rejections MUST be shown to user:**
- Even if you think they're "task-specific", present them
- The user will decide if they're reusable
- Count how many you found and report: "Found N tool rejections"
- Never say "analyzed N rejections, none reusable" without showing them

**0.5c. Apply date filter if `--days N` specified:**
- Check file modification time
- Skip files older than N days

**0.5d. Semantic Validation (Enhanced LLM Filter):**

For each extracted correction, use semantic analysis to determine if it's a REUSABLE learning.

**Preferred: Use semantic detector for accuracy:**
```python
# scripts/lib/semantic_detector.py
from lib.semantic_detector import semantic_analyze

result = semantic_analyze(message)
# Returns: is_learning, type, confidence, reasoning, extracted_learning
```

Benefits of semantic analysis:
- Works for ANY language (not just English patterns)
- Provides cleaner `extracted_learning` for CLAUDE.md
- More accurate confidence scores
- Explains reasoning for each classification

If semantic analysis is unavailable (timeout, CLI error), fall back to heuristic rules:

**CRITICAL RULES:**
1. **NEVER filter out `remember:` items** - these are explicit user requests, always present them
2. **NEVER filter out queue items** - the user explicitly captured these via hooks
3. **When in doubt, INCLUDE the learning and let user decide** - don't auto-reject borderline cases
4. **If extraction found matches, SHOW THEM** - never conclude "0 learnings" without presenting raw matches to user
5. **Tool rejections = ALWAYS SHOW** - even "task-specific" ones might have reusable elements

**REJECT ONLY if clearly:**
- A question (ends with "?")
- Pure task confirmation ("yes", "ok", "done", "looks good")
- Too vague to extract meaning ("fix it", "wrong")

**ACCEPT if it mentions:**
- Tool/technology/API names or parameters
- Flags, settings, or configuration options ("enable X", "use flag Y")
- Best practices or patterns ("always do X", "don't do Y")
- Model names or versions
- Rate limits, delays, or timing
- File paths or environment setup

**TRUST USER CORRECTIONS**: For model names, API versions, tool availability, and flag/parameter values - the user has more current knowledge than Claude's training data. Do NOT try to validate whether something "exists" or is "correct". Accept user corrections as authoritative.

**BORDERLINE → Get context first:**
If a correction seems context-specific (like "please enable that flag"), search for surrounding messages to understand WHAT flag/parameter. Often these ARE reusable learnings about API parameters.

```bash
# Get context around a correction (find line number, then show surrounding)
grep -n "enable that flag" "$SESSION_FILE" | head -1
```

For each ACCEPTED correction, create:
1. An actionable learning in imperative form (e.g., "Use gpt-5.1 for reasoning tasks" or "Enable flag X for better results")
2. Suggested scope: "global" or "project"
3. Include the actual parameter/value when possible

**0.5e. Deduplicate:**
- Collect all accepted corrections
- Remove exact duplicates
- For similar corrections, keep the most recent

**0.5f. Build working list:**
- ADD history scan results to working list (alongside any queue items from Step 1)
- Use the actionable learning you created as the proposed entry
- Use the scope suggestion (global/project) as default
- Mark source as "history-scan" or "tool-rejection"

**SANITY CHECK before proceeding:**
- Verify queue items from Step 1 are still in working list
- If queue had N items, working list must have at least N items
- If working list is empty but queue was NOT empty → BUG, re-add queue items

**MANDATORY PRESENTATION RULE:**
If your extraction (grep, search, jq) found ANY matches:
1. You MUST present them to the user - do NOT auto-conclude "0 learnings"
2. Show at least the top 10-15 raw matches for user review
3. For each match, propose: keep as learning OR skip
4. Let the USER decide what's reusable, not the LLM

**Format for presenting raw matches:**
```
═══════════════════════════════════════════════════════════
RAW MATCHES FOUND — [N] items need review
═══════════════════════════════════════════════════════════

#1 [source: session-scan | tool-rejection]
   "[raw text from extraction]"
   → Proposed: [actionable learning] | Scope: [global/project]

#2 ...
═══════════════════════════════════════════════════════════
```

Then use AskUserQuestion to let user select which to keep.

**NEVER conclude "0 learnings found" if:**
- Grep/search returned >0 matches
- Tool rejections were found but not shown
- You filtered items without user review

**0.5g. Extract Tool Execution Errors (Project-Specific Only):**

Scan session files for REPEATED tool execution errors that reveal project-specific context.

**What to extract:**
Tool execution errors (`is_error: true`) that indicate project-specific issues:
- Connection errors → Check .env for service URLs
- Module not found → Project structure/import conventions
- Environment undefined → Load .env file first
- Service-specific errors (Supabase, Postgres, Redis) → Check config

**What to EXCLUDE:**
- Claude Code guardrails ("File has not been read yet", "exceeds max tokens")
- Global Claude behavior (bash quoting, EISDIR directory confusion)
- One-off errors (only include patterns with 2+ occurrences)

**Use the extraction script:**
```bash
python scripts/extract_tool_errors.py --project "$(pwd)" --min-count 2 --json
```

Or use the utility functions directly:
```python
from lib.reflect_utils import extract_tool_errors, aggregate_tool_errors

# Extract from session files
errors = []
for session_file in session_files:
    errors.extend(extract_tool_errors(session_file, project_specific_only=True))

# Aggregate by pattern (only keep 2+ occurrences)
aggregated = aggregate_tool_errors(errors, min_occurrences=2)
```

**Semantic validation (optional):**
```python
from lib.semantic_detector import validate_tool_errors
validated = validate_tool_errors(aggregated)
```

**Add validated error patterns to working list:**
- Mark source as "tool-error"
- Use `suggested_guideline` or `refined_guideline` as the proposed entry
- Set scope to "project" (these are project-specific patterns)

**Example output:**
```
═══════════════════════════════════════════════════════════
TOOL ERROR PATTERNS — [N] project-specific issues found
═══════════════════════════════════════════════════════════

#1 [connection_refused] — 5 occurrences
   Sample: "Connection refused to localhost:5432"
   → Proposed: "Check DATABASE_URL in .env for PostgreSQL connection"

#2 [env_undefined] — 3 occurrences
   Sample: "SUPABASE_URL is not defined"
   → Proposed: "Load .env file before accessing environment variables"
═══════════════════════════════════════════════════════════
```

If tool error patterns are found, add them to the working list alongside user corrections.

- Continue to Step 3 (Project-Aware Filtering) with COMBINED list (queue + history + tool-errors)

### Step 1: Load and Validate
- Read the queue from `~/.claude/learnings-queue.json`
- Add all queue items to the working list (mark source as "queued")
- **IMPORTANT**: Even if queue is empty, continue if `--scan-history` will add items
- Only exit early if: queue is empty AND not doing history scan AND user declines manual capture

### Step 1.5: Semantic Validation (Queue Items)

After loading queue items, validate them using AI-powered semantic analysis. This provides:
- **Multi-language support** — understands corrections in any language, not just English patterns
- **Better accuracy** — filters out false positives from regex detection
- **Cleaner learnings** — extracts concise, actionable statements for CLAUDE.md

**1.5a. Run semantic analysis on each queue item:**

Use the semantic detector (via `claude -p`) to analyze each queued message:

```python
# scripts/lib/semantic_detector.py provides:
from lib.semantic_detector import validate_queue_items

# For each item, semantic analysis returns:
# {
#   "is_learning": bool,           # Should this be kept?
#   "type": "correction"|"positive"|"explicit"|null,
#   "confidence": 0.0-1.0,         # AI's confidence score
#   "reasoning": str,              # Why it was classified this way
#   "extracted_learning": str      # Clean, actionable statement
# }
```

**1.5b. Filter and enhance queue items:**

For each queue item:
1. Call semantic analysis on `item["message"]`
2. If `is_learning == false` → remove from working list (not a reusable learning)
3. If `is_learning == true`:
   - Update confidence: `max(original_confidence, semantic_confidence)`
   - Add `extracted_learning` for cleaner CLAUDE.md entries
   - Add `semantic_type` to preserve classification

**1.5c. Fallback behavior:**

If semantic analysis fails (timeout, Claude CLI not available, API error):
- **Keep the original item** with its regex-based classification
- Log: "Semantic validation unavailable, using pattern-based detection"
- Proceed normally with regex confidence scores

**1.5d. Report filtering results:**

Show what was filtered:
```
═══════════════════════════════════════════════════════════
SEMANTIC VALIDATION — [N] items analyzed
═══════════════════════════════════════════════════════════
  ✓ [M] confirmed as learnings
  ✗ [K] filtered (not reusable learnings)

Filtered items (skipped):
  - "Hello, how are you?" — [greeting, not a learning]
  - "Can you help me?" — [question, not a learning]
═══════════════════════════════════════════════════════════
```

**NOTE**: `remember:` items are ALWAYS kept regardless of semantic analysis — explicit user requests are never filtered.

### Step 1.6: Auto Memory Enrichment

Scan auto memory for entries that may deserve "promotion" to CLAUDE.md, and route low-confidence items downward.

**1.6a. Check auto memory for promotion candidates:**

```python
from scripts.lib.reflect_utils import read_auto_memory
auto_entries = read_auto_memory()
# Look for entries that have been validated by repeated use
```

If auto memory entries exist, scan for patterns that appear in multiple topic files or have been manually confirmed — these are candidates for promotion to CLAUDE.md.

**1.6b. Route low-confidence queue items to auto memory:**

For items with confidence 0.60-0.74 that passed semantic validation:
- Offer auto memory as a destination instead of CLAUDE.md
- Auto memory is a "staging area" — items can be promoted later via `/reflect --organize`

```
Learning: "Try using batch mode for large datasets" (confidence: 0.65)
→ Suggested destination: Auto Memory (model-preferences.md)
  Reason: Low confidence — store in auto memory for now, promote later if confirmed
```

Use AskUserQuestion when routing to auto memory:
```json
{
  "questions": [{
    "question": "Low-confidence learning — where should it go?",
    "header": "Route",
    "multiSelect": false,
    "options": [
      {"label": "Auto Memory (Recommended)", "description": "Store in auto memory for later promotion"},
      {"label": "CLAUDE.md", "description": "Add to CLAUDE.md despite low confidence"},
      {"label": "Skip", "description": "Don't store this learning"}
    ]
  }]
}
```

### Step 2: Session Reflection (Enhanced with History Analysis)

**Note**: This step is for analyzing the CURRENT session only (when NOT using `--scan-history`).
If `--scan-history` was passed, skip to Step 3 with results from Step 0.5.

Analyze the current session for corrections missed by real-time hooks:

**2a. Find current session file:**

List session files for this project (most recent first):
```bash
ls -lt ~/.claude/projects/ | grep -i "$(basename $(pwd))"
```

Then list files in that folder and pick the most recent non-agent file:
```bash
ls -lt ~/.claude/projects/[PROJECT_FOLDER]/*.jsonl | head -5
```

Agent files (`agent-*.jsonl`) are sub-conversations; focus on main session files for current session analysis.

**2b. Extract tool rejections (HIGH confidence corrections):**

Search the current session file for `toolUseResult` fields containing "user said:" followed by feedback. These are high-confidence corrections.

- "user said:" followed by empty content = rejection without feedback, skip these
- Extract the feedback text after "user said:" for processing

**2c. Extract user messages with correction patterns:**

Search the current session file for user messages matching correction patterns. Use the same patterns from Step 0.5b. Remember:
- Filter out `isMeta: true` entries (command expansions like /reflect itself)
- Apply language-specific patterns if conversation is non-English

**2d. Also reflect on conversation context:**
- Were there any corrections or patterns not explicitly queued?
- Model names, API patterns, tool usage mistakes, project conventions?
- Implicit corrections (e.g., "Actually, the API returns...")

**2e. Semantic Validation (LLM Filter):**

If there are extracted corrections from 2b or 2c, use semantic analysis for accurate classification:

```python
from lib.semantic_detector import semantic_analyze
result = semantic_analyze(message)
# Use result["is_learning"], result["extracted_learning"], result["confidence"]
```

If semantic analysis is unavailable, fall back to heuristic evaluation:
- REJECT questions, one-time tasks, context-specific items, vague feedback
- ACCEPT tool recommendations, patterns, conventions, model corrections
- Create actionable learnings in imperative form with scope suggestions

**2f. Add findings to working list:**
For each ACCEPTED learning:
- Use the actionable learning you created as the proposed entry
- Use the scope suggestion (global/project) as default
- Add to working list alongside queued items
- Mark source type:
  - "queued" — from hooks/explicit remember:
  - "session-scan" — from message pattern matching
  - "tool-rejection" — from tool rejections (HIGH confidence)

### Step 3: Project-Aware Filtering

Get current project path. For each queue item, compare `item.project` with current project:

**CASE A: Same project**
- Show normally
- Offer: [a]pprove | [e]dit | [s]kip
- If approve, ask scope: [p]roject | [g]lobal | [b]oth

**CASE B: Different project, looks GLOBAL**
(message contains: gpt-*, claude-*, model names, general patterns like "always/never")
- Show with warning: "⚠️ FROM DIFFERENT PROJECT"
- Show: "Captured in: [original-project]"
- Offer: [g]lobal | [s]kip (NOT project - wrong context)

**CASE C: Different project, looks PROJECT-SPECIFIC**
(message contains: specific DB names, file paths, project-specific tools)
- Auto-skip with note: "Skipping project-specific learning from [other-project]"
- Offer: [f]orce to add to global anyway

**Heuristics:**
- `gpt-[0-9]` or `claude-` → GLOBAL (model name)
- `always|never|don't` + generic verb → GLOBAL (general rule)
- Specific tool/DB/service names → PROJECT-SPECIFIC
- File paths → PROJECT-SPECIFIC

### Step 3.3: Skill Context Detection (AI-Powered)

For each learning, reason about whether it relates to an **active skill**.

**IMPORTANT: Use reasoning, not pattern matching.**

Read the session context around the correction. Think:
- Was a skill/command (e.g., `/deploy`, `/commit`) invoked before this correction?
- Does the correction relate to HOW that skill should work?
- Would this correction be better as an improvement to the skill file itself?

**Example reasoning:**
```
Learning: "always run tests before deploying"
Session context: User ran /deploy, then corrected me

My analysis: This correction happened right after /deploy was invoked.
The user wants the deploy skill to include running tests.
This should be offered as a skill improvement, not a CLAUDE.md entry.
```

**For each skill-related learning, add metadata:**
```json
{
  "skill_context": {
    "skill_name": "deploy",
    "skill_file": "commands/deploy.md",
    "reason": "Correction followed /deploy invocation"
  }
}
```

**Detection approach:**
1. Look for `/command` patterns in recent session messages
2. Reason about whether the correction relates to that command's workflow
3. Check if `commands/[skill-name].md` exists in the project

**If skill context detected:**
- Mark the learning with skill metadata
- In Step 5, offer routing options: skill file | CLAUDE.md | both

**If NO skill context detected:**
- Continue with normal CLAUDE.md routing

### Step 3.5: Semantic Deduplication (Within Queue)

Before checking against CLAUDE.md, consolidate similar learnings within the current batch.

**3.5a. Group by semantic similarity:**

Analyze all learnings in the working list. Look for entries that:
- Reference the same tool, model, or concept
- Give similar advice (even with different wording)
- Could be consolidated into a single, clearer entry

**Example - Before consolidation:**
```
1. "Use gpt-5.1 for complex tasks"
2. "Prefer gpt-5.1 over gpt-5 for reasoning"
3. "gpt-5.1 is better for hard problems"
```

**Example - After consolidation:**
```
1. "Use gpt-5.1 for complex reasoning (replaces gpt-5)"
```

**3.5b. Present consolidation proposals:**

If similar learnings are detected, show:
```
═══════════════════════════════════════════════════════════
SIMILAR LEARNINGS DETECTED
═══════════════════════════════════════════════════════════

These 3 learnings appear related:
  #2: "Use gpt-5.1 for complex tasks"
  #5: "Prefer gpt-5.1 over gpt-5 for reasoning"
  #7: "gpt-5.1 is better for hard problems"

Proposed consolidation:
  → "Use gpt-5.1 for complex reasoning tasks (replaces gpt-5)"

═══════════════════════════════════════════════════════════
```

**3.5c. Use AskUserQuestion for consolidation:**

```json
{
  "questions": [{
    "question": "Consolidate these 3 similar learnings into one?",
    "header": "Dedupe",
    "multiSelect": false,
    "options": [
      {"label": "Yes, consolidate", "description": "Merge into: 'Use gpt-5.1 for complex reasoning tasks'"},
      {"label": "Keep separate", "description": "Add all 3 as individual entries"},
      {"label": "Edit consolidation", "description": "Let me modify the merged text"}
    ]
  }]
}
```

**3.5d. Consolidation rules:**
- Keep highest confidence score from the group
- Combine decay_days (use longest)
- Mark source as "consolidated"
- If user chooses "Edit", allow them to provide custom text

**3.5e. Skip if no duplicates:**
- If all learnings are semantically distinct, proceed to Step 4
- Only show consolidation UI when similar entries are detected

### Step 4: Duplicate Detection with Line Numbers (All Memory Tiers)

For each learning kept after filtering, search ALL memory tiers:

```bash
# CLAUDE.md files
grep -n -i "keyword" ~/.claude/CLAUDE.md
grep -n -i "keyword" CLAUDE.md
grep -n -i "keyword" CLAUDE.local.md 2>/dev/null

# Rule files
grep -rn -i "keyword" .claude/rules/ 2>/dev/null
grep -rn -i "keyword" ~/.claude/rules/ 2>/dev/null

# Auto memory
grep -rn -i "keyword" ~/.claude/projects/PROJECT_FOLDER/memory/ 2>/dev/null
```

Or use the cross-tier deduplication utility:
```python
from scripts.lib.reflect_utils import read_all_memory_entries
entries = read_all_memory_entries()
# Returns [{text, source_file, source_type, line_number}, ...]
# Search entries for semantic similarity to each learning
```

If duplicate found:
- Show: "⚠️ SIMILAR in [source_type] [source_file]: Line [N]: [content]"
- Offer: [m]erge | [r]eplace | [a]dd anyway | [s]kip

### Step 5: Present Summary and Get User Decision

**5a. Display condensed summary table:**

Show all learnings in a compact table format:

```
════════════════════════════════════════════════════════════
LEARNINGS SUMMARY — [N] items found
════════════════════════════════════════════════════════════

┌────┬─────────────────────────────────────────┬──────────┬────────┐
│ #  │ Learning                                │ Target   │ Status │
├────┼─────────────────────────────────────────┼──────────┼────────┤
│ 1  │ Use DB for persistent storage           │ project  │ ✓ new  │
│ 2  │ Backoff on actual errors only           │ global   │ ✓ new  │
│ 3  │ Run tests before deploying              │ /deploy  │ ⚡skill │
│ ...│ ...                                     │ ...      │ ...    │
└────┴─────────────────────────────────────────┴──────────┴────────┘

Destinations: [N] → Global, [M] → Project, [K] → Skills
Duplicates: [L] items will be merged with existing entries
```

**5a.1. Skill-Related Learnings (if any detected):**

If any learnings have `skill_context` metadata from Step 3.3, show them separately:

```
════════════════════════════════════════════════════════════
SKILL IMPROVEMENTS DETECTED
════════════════════════════════════════════════════════════

These learnings appear related to specific skills:

#3: "Run tests before deploying"
   → Relates to: /deploy (commands/deploy.md)
   → Reason: Correction followed /deploy invocation

#7: "Include file count in commit message"
   → Relates to: /commit (commands/commit.md)
   → Reason: Correction during commit workflow

════════════════════════════════════════════════════════════
```

**5a.2. Skill Routing Question:**

For each skill-related learning, use AskUserQuestion:
```json
{
  "questions": [{
    "question": "Learning #3 relates to /deploy. Where should it go?",
    "header": "Route",
    "multiSelect": false,
    "options": [
      {"label": "Skill file (Recommended)", "description": "Add to commands/deploy.md to improve the skill"},
      {"label": "CLAUDE.md", "description": "Add to project CLAUDE.md as general guidance"},
      {"label": "Both", "description": "Add to skill file AND CLAUDE.md"},
      {"label": "Skip", "description": "Don't add this learning anywhere"}
    ]
  }]
}
```

Track routing decisions for Step 7.

**5b. Use AskUserQuestion for strategy:**

Use the AskUserQuestion tool:
```json
{
  "questions": [{
    "question": "How would you like to process these [N] learnings?",
    "header": "Action",
    "multiSelect": false,
    "options": [
      {"label": "Apply all (Recommended)", "description": "Add [X] new entries, merge [K] duplicates with recommended scopes"},
      {"label": "Select which to apply", "description": "Choose specific learnings from grouped lists"},
      {"label": "Review details first", "description": "Show full details for each learning before deciding"},
      {"label": "Skip all", "description": "Don't apply any learnings, clear the queue"}
    ]
  }]
}
```

**5c. Handle user selection:**

- **"Apply all"** → Proceed to Step 6 (Final Confirmation)
- **"Select which to apply"** → Go to Step 5.1 (Selection Mode)
- **"Review details first"** → Show full learning cards (format below), then return to 5b
- **"Skip all"** → Go to Step 8 (Clear Queue)

**Full learning card format (for "Review details first"):**
```
════════════════════════════════════════════════════════════
LEARNING [N] of [TOTAL] — [source: queued/session-scan/tool-rejection]
════════════════════════════════════════════════════════════
Original message:
  "[the user's original text]"

Proposed addition:
┌──────────────────────────────────────────────────────────┐
│ ## [Section Name]                                        │
│ - [Exact bullet point that will be added]                │
└──────────────────────────────────────────────────────────┘

Duplicate check:
  ✓ None found
  OR
  ⚠️ SIMILAR in [global/project] CLAUDE.md:
     Line [N]: "[existing content]"
════════════════════════════════════════════════════════════
```

### Step 5.1: Selection Mode (if user chose "Select which to apply")

Group learnings by destination and use AskUserQuestion with multiSelect.

**Rules:**
- Split into multiple questions if >4 items per destination
- Use short labels: "#{N} {short_title}" (max 20 chars)
- Use descriptions for full learning text (max 80 chars)

**Example for GLOBAL learnings:**
```json
{
  "questions": [
    {
      "question": "Select GLOBAL learnings to apply:",
      "header": "Global",
      "multiSelect": true,
      "options": [
        {"label": "#2 Backoff errors", "description": "Implement backoff only on actual errors, not artificial delays"},
        {"label": "#3 DB cache", "description": "Use local database cache to minimize data fetching"},
        {"label": "#4 Batch+delays", "description": "Use batching with stochastic delays for API rate limits"},
        {"label": "#5 Use venv", "description": "Always use virtual environments for Python projects"}
      ]
    }
  ]
}
```

**If >4 global items:** Add second question with header "Global+"

**Example for PROJECT learnings:**
```json
{
  "questions": [
    {
      "question": "Select PROJECT learnings to apply:",
      "header": "Project",
      "multiSelect": true,
      "options": [
        {"label": "#1 DB storage", "description": "Use database for persistent tracking data"},
        {"label": "#6 DB ports", "description": "Assign unique ports per database instance"}
      ]
    }
  ]
}
```

**Selection rules:**
- Items NOT selected will be skipped
- Continue to Step 6 with selected items only

### Step 6: Final Confirmation

**6a. Show summary of changes:**
```
════════════════════════════════════════════════════════════
SUMMARY: [N] changes ready to apply
════════════════════════════════════════════════════════════

Project CLAUDE.md ([path]):
  Line [N]: UPDATE "[old]" → "[new]"
  After line [N]: ADD "[new entry]"

Global CLAUDE.md (~/.claude/CLAUDE.md):
  Line [N]: REPLACE "[old]" → "[new]"
  After line [N]: ADD "[new entry]"

Skill Files:
  commands/deploy.md: ADD "Run tests before build step"
  commands/commit.md: ADD "Include file count in message"

Skipped: [N] learnings (including [M] from other projects)
════════════════════════════════════════════════════════════
```

**6b. Use AskUserQuestion for confirmation:**
```json
{
  "questions": [{
    "question": "Apply [N] learnings to target files?",
    "header": "Confirm",
    "multiSelect": false,
    "options": [
      {"label": "Yes, apply all", "description": "[X] to Global, [Y] to Project, [Z] to Skills"},
      {"label": "Go back", "description": "Return to selection to adjust"},
      {"label": "Cancel", "description": "Don't apply anything, keep queue"}
    ]
  }]
}
```

**6c. Handle response:**
- **"Yes, apply all"** → Proceed to Step 7
- **"Go back"** → Return to Step 5b
- **"Cancel"** → Exit without changes (keep queue intact)

### Step 7: Apply Changes

Only after final confirmation:

**7a. Apply to CLAUDE.md (Primary Targets):**
1. Read current CLAUDE.md files
2. Use Edit tool with precise old_string from detected line numbers
3. For new entries, add after the relevant section header

**7a.1. Apply to Rule Files (if any routed to rules):**

For learnings routed to `.claude/rules/*.md`:

1. Check if the target rule file exists; if not, create it:
   - Ask user to confirm filename for new rule files
   - Naming conventions: `guardrails.md`, `model-preferences.md`, `coding-style.md`, `testing.md`, etc.
2. If the rule is path-specific, add YAML frontmatter:
   ```markdown
   ---
   paths:
     - "src/"
     - "lib/"
   ---
   ```
3. Append the learning as a bullet point under an appropriate heading
4. For `~/.claude/rules/*.md` (user-level rules), use the same approach

**7a.2. Apply to Auto Memory (if low-confidence or exploratory):**

For learnings routed to auto memory (typically confidence 0.60-0.74):

1. Use `suggest_auto_memory_topic()` to determine filename:
   ```python
   from scripts.lib.reflect_utils import suggest_auto_memory_topic, get_auto_memory_path
   topic = suggest_auto_memory_topic(learning_text)  # e.g., "model-preferences"
   memory_dir = get_auto_memory_path()
   ```
2. Create memory directory if missing: `memory_dir.mkdir(parents=True, exist_ok=True)`
3. Write/append to topic file (`{topic}.md`) in markdown format:
   ```markdown
   # Model Preferences
   - Use gpt-5.1 for reasoning tasks (confidence: 0.65, 2026-02-12)
   ```
4. Auto memory entries can later be "promoted" to CLAUDE.md via `/reflect --organize`

**7b. Apply to Skill Files (if any routed to skills):**

For learnings routed to skill files in Step 5a.2:

1. Read the skill file (e.g., `commands/deploy.md`)
2. Reason about WHERE the learning fits in the skill:
   - Is it a new step in the workflow? → Add to steps section
   - Is it a guardrail/constraint? → Add to guardrails section
   - Is it context/setup? → Add to context section
3. Use Edit tool to insert the learning appropriately

**Example skill file update:**
```markdown
## Steps

1. Run tests                    ← NEW (added from learning)
2. Build the project
3. Push to production
4. Notify Slack

## Guardrails
- Always verify tests pass before proceeding  ← Could also go here
```

**Important:**
- Preserve the skill's existing structure
- Add learnings where they make semantic sense
- Use your reasoning to determine placement (not hardcoded rules)

**7c. Apply to AGENTS.md (if exists):**

Check if AGENTS.md exists:
```bash
test -f AGENTS.md && echo "AGENTS.md found"
```

If AGENTS.md exists, apply the SAME learnings using this format:

```markdown
## Claude-Reflect Learnings

<!-- Auto-generated by claude-reflect. Do not edit this section manually. -->

### Model Preferences
- Use gpt-5.1 for reasoning tasks

### Tool Usage
- Use local database cache to minimize API calls

<!-- End claude-reflect section -->
```

**Update Strategy:**
- Look for existing `<!-- Auto-generated by claude-reflect` marker
- If found: REPLACE the entire section (from marker to `<!-- End claude-reflect section -->`)
- If not found: APPEND section at the end of the file
- Always preserve user's existing content outside the marked section

### Step 8: Clear Queue

```bash
echo "[]" > ~/.claude/learnings-queue.json
```

### Step 9: Confirm

```
════════════════════════════════════════════════════════════
DONE: Applied [N] learnings
════════════════════════════════════════════════════════════
  ✓ ~/.claude/CLAUDE.md    [N] entries
  ✓ ./CLAUDE.md            [N] entries
  ✓ AGENTS.md              [N] entries (if exists)
  ⚡ commands/deploy.md     [N] skill improvements
  ⚡ commands/commit.md     [N] skill improvements

  Skipped: [N]
════════════════════════════════════════════════════════════
```

### Step 10: Mark Initialized (Per-Project)

Create marker file for THIS project so first-run detection won't trigger again.
Use the PROJECT_FOLDER you found in First-Run Detection:

```bash
touch ~/.claude/projects/PROJECT_FOLDER/.reflect-initialized
```

Replace PROJECT_FOLDER with the actual folder name (e.g., `-Users-bob-myproject`).

## Formatting Rules

- **Bullets, not prose**: Keep entries as single bullet points
- **Actionable**: "Use X for Y" not "X is better than Y"
- **Concise**: Max 2 lines per entry
- **Examples when helpful**: `(e.g., gpt-5.2 not gpt-5.1)`

## Section Headers

Use these standard headers:
- `## LLM Model Recommendations` — model names, versions
- `## Tool Usage` — MCP, APIs, which tool for what
- `## Project Conventions` — coding style, patterns
- `## Guardrails` — constraints and "don't do X" rules
- `## Common Errors to Avoid` — gotchas, mistakes
- `## Environment Setup` — venv, configs, paths

### Rule File Mapping

When routing learnings to `.claude/rules/` files, use this mapping:

| Learning Type | Suggested Rule File | Create If Missing |
|---------------|--------------------|--------------------|
| Guardrails / "don't do X" | `guardrails.md` | Yes |
| Model preferences | `model-preferences.md` | Yes |
| Coding style / formatting | `coding-style.md` | Yes |
| Testing conventions | `testing.md` | Yes |
| Path-specific rules | `{context}.md` with `paths:` frontmatter | Ask user |

**YAML Frontmatter for Path-Scoped Rules:**

When a learning applies only to specific directories, create the rule file with frontmatter:
```markdown
---
paths:
  - "src/api/"
  - "src/services/"
---

# API Conventions
- Always use async/await for API handlers
- Return proper HTTP status codes
```

Rules without `paths:` frontmatter apply globally within the project.

### Guardrail Routing

Learnings with `type: "guardrail"` are special corrections about unwanted behavior. These should be routed to the `## Guardrails` section in CLAUDE.md.

**Guardrail patterns detected by `reflect_utils.py`:**
- "don't add X unless I ask" → `dont-unless-asked`
- "only change what I asked" → `only-what-asked`
- "stop refactoring unrelated code" → `stop-unrelated`
- "don't over-engineer" → `dont-over-engineer`
- "leave X alone" → `leave-alone`
- "minimal changes only" → `minimal-changes`

**When presenting guardrail learnings:**
```
═══════════════════════════════════════════════════════════
GUARDRAIL DETECTED — Constraint about unwanted behavior
═══════════════════════════════════════════════════════════

Original: "don't add docstrings unless I explicitly ask"
Pattern: dont-unless-asked (confidence: 0.90)

Proposed entry for ## Guardrails:
┌────────────────────────────────────────────────────────┐
│ - Don't add docstrings to code unless explicitly asked │
└────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════
```

**Formatting guardrails:**
- Present as constraints/rules rather than preferences
- Use imperative negative form: "Don't X" or "Only do Y when Z"
- Keep concise and actionable
- Route to `## Guardrails` section (create if doesn't exist)

## Size Check

If CLAUDE.md exceeds 150 lines, warn:
```
Note: CLAUDE.md is [N] lines. Consider:
  - /reflect --dedupe to consolidate similar entries
  - /reflect --organize to redistribute across memory tiers
```
