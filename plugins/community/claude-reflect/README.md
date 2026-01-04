# claude-reflect

A self-learning system for Claude Code that captures corrections, positive feedback, and preferences — then syncs them to CLAUDE.md and AGENTS.md.

## What it does

When you correct Claude Code during a session ("no, use gpt-5.1 not gpt-5", "use database for caching"), these corrections are captured and can be added to your CLAUDE.md files so Claude remembers them in future sessions.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  You correct    │ ──► │  Hook captures  │ ──► │  /reflect adds  │
│  Claude Code    │     │  to queue       │     │  to CLAUDE.md   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
      (automatic)            (automatic)            (manual review)
```

## Installation

```bash
# Add the marketplace
claude plugin marketplace add bayramannakov/claude-reflect

# Install the plugin
claude plugin install claude-reflect@claude-reflect-marketplace

# IMPORTANT: Restart Claude Code to activate the plugin
```

After installation, **restart Claude Code** (exit and reopen). Then hooks auto-configure and commands are ready.

> **First run?** When you run `/reflect` for the first time, you'll be prompted to scan your past sessions for learnings.

### Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed
- `jq` for JSON processing (`brew install jq` on macOS)
- `python3` (included on most systems)

## Commands

| Command | Description |
|---------|-------------|
| `/reflect` | Process queued learnings with human review |
| `/reflect --scan-history` | Scan ALL past sessions for missed learnings |
| `/reflect --dry-run` | Preview changes without applying |
| `/reflect --targets` | Show detected config files (CLAUDE.md, AGENTS.md) |
| `/reflect --review` | Show queue with confidence scores and decay status |
| `/reflect --dedupe` | Find and consolidate similar entries in CLAUDE.md |
| `/skip-reflect` | Discard all queued learnings |
| `/view-queue` | View pending learnings without processing |

## How It Works

### Two-Stage Process

**Stage 1: Capture (Automatic)**

Hooks run automatically to detect and queue corrections:

| Hook | Trigger | Purpose |
|------|---------|---------|
| `capture-learning.sh` | Every prompt | Detects correction patterns and queues them |
| `check-learnings.sh` | Before compaction | Blocks compaction if queue has items |
| `post-commit-reminder.sh` | After git commit | Reminds to run /reflect after completing work |

**Stage 2: Process (Manual)**

Run `/reflect` to review and apply queued learnings to CLAUDE.md.

### Pattern Detection

The capture hook detects corrections AND positive feedback:

**Corrections** (what went wrong):
- `"no, use X"` / `"don't use Y"`
- `"actually..."` / `"I meant..."`
- `"use X not Y"` / `"that's wrong"`

**Positive patterns** (what works):
- `"Perfect!"` / `"Exactly right"`
- `"That's what I wanted"` / `"Great approach"`
- `"Keep doing this"` / `"Nailed it"`

**Explicit markers**:
- `"remember:"` — highest confidence

Each captured learning has a **confidence score** (0.60-0.95) based on pattern strength. Higher confidence = more likely to be a real learning.

### Human Review

When you run `/reflect`, Claude presents a summary table:

```
════════════════════════════════════════════════════════════
LEARNINGS SUMMARY — 5 items found
════════════════════════════════════════════════════════════

┌────┬─────────────────────────────────────────┬──────────┬────────┐
│ #  │ Learning                                │ Scope    │ Status │
├────┼─────────────────────────────────────────┼──────────┼────────┤
│ 1  │ Use gpt-5.1 for reasoning tasks         │ global   │ ✓ new  │
│ 2  │ Database for persistent storage         │ project  │ ✓ new  │
└────┴─────────────────────────────────────────┴──────────┴────────┘
```

You choose:
- **Apply all** - Accept recommended changes
- **Select which** - Pick specific learnings
- **Review details** - See full context before deciding

### Multi-Target Sync

Approved learnings are synced to:
- `~/.claude/CLAUDE.md` (global - applies to all projects)
- `./CLAUDE.md` (project-specific)
- `AGENTS.md` (if exists - works with Codex, Cursor, Aider, Jules, Zed, Factory)

Run `/reflect --targets` to see which files will be updated.

## Uninstall

```bash
claude plugin uninstall claude-reflect@claude-reflect-marketplace
```

## File Structure

```
claude-reflect/
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest (auto-registers hooks)
├── commands/
│   ├── reflect.md          # Main command
│   ├── skip-reflect.md     # Discard queue
│   └── view-queue.md       # View queue
├── hooks/
│   └── hooks.json          # Auto-configured when plugin installed
├── scripts/
│   ├── capture-learning.sh       # Hook: detect corrections
│   ├── check-learnings.sh        # Hook: pre-compact check
│   ├── post-commit-reminder.sh   # Hook: post-commit reminder
│   ├── extract-session-learnings.sh
│   └── extract-tool-rejections.sh
└── SKILL.md                # Skill context for Claude
```

## Features

### Historical Scan

First time using claude-reflect? Run:

```bash
/reflect --scan-history
```

This scans all your past sessions for corrections you made, so you don't lose learnings from before installation.

### Smart Filtering

Claude filters out:
- Questions (not corrections)
- One-time task instructions
- Context-specific requests
- Vague/non-actionable feedback

Only reusable learnings are kept.

### Duplicate Detection

Before adding a learning, existing CLAUDE.md content is checked. If similar content exists, you can:
- Merge with existing entry
- Replace the old entry
- Skip the duplicate

### Semantic Deduplication

Over time, CLAUDE.md can accumulate similar entries. Run `/reflect --dedupe` to:
- Find semantically similar entries (even with different wording)
- Propose consolidated versions
- Clean up redundant learnings

Example:
```
Before:
  - Use gpt-5.1 for complex tasks
  - Prefer gpt-5.1 for reasoning
  - gpt-5.1 is better for hard problems

After:
  - Use gpt-5.1 for complex reasoning tasks
```

## Tips

1. **Use explicit markers** for important learnings:
   ```
   remember: always use venv for Python projects
   ```

2. **Run /reflect after git commits** - The hook reminds you, but make it a habit

3. **Historical scan on new machines** - When setting up a new dev environment:
   ```
   /reflect --scan-history --days 90
   ```

4. **Project vs Global** - Model names and general patterns go global; project-specific conventions stay in project CLAUDE.md

## Contributing

Pull requests welcome! Please read the contributing guidelines first.

## License

MIT
