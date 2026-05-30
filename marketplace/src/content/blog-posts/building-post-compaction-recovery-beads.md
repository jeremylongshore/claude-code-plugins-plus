---
title: "Building Post-Compaction Recovery for AI Agent Workflows with Beads"
description: "How to solve the context loss problem in AI agent workflows using git-based task persistence. A deep dive into implementing beads for post-compaction recovery with real troubleshooting examples."
date: "2025-12-28"
tags: ["ai-development", "task-tracking", "agent-workflows", "git", "automation", "claude-code"]
featured: false
---
When Claude Code compacts (summarizes) conversations, you lose critical context about what you were working on. Here's how I solved that problem with a git-based task persistence system - and the debugging journey that made it work.

## The Problem: Context Loss After Compaction

Claude Code has unlimited context through automatic summarization. When your conversation gets long, it "compacts" by summarizing earlier parts. This is great for memory efficiency, but creates a critical problem:

**When you start a fresh session, you've lost:**

- What task you were working on
- What state things were in
- What the next step was
- What failed attempts you already tried

Every experienced developer has hit this: "Wait, what was I doing before lunch?"

## The Solution: Git-Persisted Task State

I implemented a post-compaction recovery system using [beads](https://github.com/steveyegge/beads) - a task tracking system that persists state in git. The key insight: **if it's in git, it survives compaction**.

Here's what the universal `/beads` command does:

```bash
/beads  # Run this at session start
```

**Auto-detects and executes:**

1. First time? → Full setup (init, hooks, sync branch)
2. Maintenance needed? → Update configuration
3. Already set up? → Recover your context

## The Implementation Journey

Let me show you the real debugging process - this wasn't a clean first attempt.

### Attempt 1: Run the Command

```bash
bd sync
```

**Result:** Failed immediately.

```
Error pulling from sync branch: failed to create worktree:
fatal: 'main' is already used by worktree
```

**What I learned:** The sync branch was misconfigured, pointing to `main` instead of `beads-sync`. Can't have two worktrees on the same branch.

### Attempt 2: Fix the Sync Branch Configuration

```bash
bd config set sync.branch beads-sync
```

**Result:** Config updated, but sync still failed.

```
fatal: couldn't find remote ref beads-sync
```

**What I learned:** The configuration was fixed, but the branch didn't exist yet in git.

### Attempt 3: Create the Missing Branch

```bash
git checkout -b beads-sync
git checkout -
```

**Result:** Branch created, but needed to verify hooks.

### Attempt 4: Install Git Hooks

```bash
bd hooks install
```

**Result:** 4 hooks installed successfully.

```
✓ Git hooks installed successfully

Installed hooks:
  - pre-push
  - post-checkout
  - pre-commit
  - post-merge
```

**What I learned:** Hooks provide automatic sync on git operations. Critical for keeping task state synchronized.

### Attempt 5: Sync Again

```bash
bd sync
```

**Result:** SUCCESS!

```
→ Exporting pending changes to JSONL...
→ Pulling from sync branch 'beads-sync'...
→ Importing updated JSONL...
Import complete: 0 created, 0 updated, 245 unchanged

✓ Sync complete
```

## How It Works: The Architecture

The beads system uses a clever multi-layer architecture:

**1. Local SQLite Database**

- Fast local operations
- Full query capabilities
- Location: `.beads/beads.db`

**2. JSONL Export**

- Human-readable task format
- Git-friendly (line-based diffs)
- Location: `.beads/issues.jsonl`

**3. Git Sync Branch**

- Separate branch for task state (`beads-sync`)
- Independent from code changes
- Automatic sync via git hooks

**4. Git Hooks**

- `pre-commit`: Flush pending changes before commit
- `post-merge`: Import updates after pulls
- `pre-push`: Export database before pushing
- `post-checkout`: Ensure consistency on branch switches

## The Recovery Flow

Here's what happens when you start a fresh session after compaction:

```bash
# Session starts - context is gone
/beads

# Auto-detection phase
✓ Beads found (.beads/ exists)
⚠ Sync branch not configured - will set up

# Maintenance phase
bd config set sync.branch beads-sync
git checkout -b beads-sync && git checkout -
bd hooks install

# Recovery phase
bd sync  # Pull latest task state from git

# Show active work
bd list --status in_progress
```

**Output:**

```
Active Work:
claude-code-plugins-7c0 [P1] Phase 1: Gemini Integration
```

**Immediately you know:** "I was working on Gemini integration for the skill generator."

## The Power of Git-Based Persistence

Why git instead of a database or API?

**1. Works offline** - No API dependencies
**2. Version controlled** - Full task history
**3. Survives compaction** - Git state persists across sessions
**4. Familiar workflow** - Uses standard git operations
**5. Conflict resolution** - Built-in 3-way merge for JSONL

Example conflict resolution:

```bash
git config merge.beads.driver "bd merge-driver %O %A %B %P"
git config merge.beads.name "Beads JSONL 3-way merge"
```

The `.gitattributes` configuration:

```
.beads/issues.jsonl merge=beads
```

This ensures beads handles JSONL conflicts intelligently, preserving both local and remote changes.

## Real-World Results

After implementing this system in the claude-code-plugins project:

**Task Statistics:**

- 245 total tasks tracked
- 207 completed (84% success rate)
- 38 currently open
- 0 tasks lost to compaction

**Recovery Time:**

- Before: 5-10 minutes reconstructing context
- After: < 30 seconds with `/beads` command

**False Start Prevention:**

- Before: Repeated failed attempts (already tried that!)
- After: Full task history shows what was already attempted

## Key Implementation Lessons

**1. Auto-detection is critical**
Don't make users remember different commands for different states. One command that figures out what's needed.

**2. Idempotency matters**
Running `/beads` multiple times should be safe. No destructive operations.

**3. Show the journey**
The debugging process taught me more than the final solution. Document failed attempts.

**4. Git hooks automate persistence**
Manual sync is error-prone. Hooks ensure task state stays synchronized.

**5. Separate branches for task state**
Keeps task tracking independent from code changes. No pollution of main branch history.

## The Complete Setup

Here's the full setup for any project:

```bash
# Initialize beads
bd init

# Install git hooks
bd hooks install

# Configure sync branch
bd config set sync.branch beads-sync

# Create sync branch
git checkout -b beads-sync
git checkout -

# Configure merge driver
echo ".beads/issues.jsonl merge=beads" >> .gitattributes
git config merge.beads.driver "bd merge-driver %O %A %B %P"
git config merge.beads.name "Beads JSONL 3-way merge"

# Initial sync
bd sync
```

**After that, just run `/beads` at every session start.**

## What I Learned

**1. Context loss is solvable**
Git persistence + auto-detection = reliable recovery

**2. The journey matters**
Five failed attempts taught me about worktrees, sync branches, and git hooks

**3. Debugging is iterative**
Each error revealed the next configuration issue

**4. Automation beats manual**
Git hooks eliminated the "did I sync?" question

**5. Make it universal**
One command for all states reduces cognitive load

## Related Posts

- AI-Assisted Technical Writing: From Case Study to Published Portfolio in 30 Minutes
- [Distributed Systems Architecture Patterns Cheat Sheet](https://startaitools.com/posts/distributed-systems-architecture-patterns-cheat-sheet/)

## What's Next

The `/beads` command now handles:

- ✅ First-time setup
- ✅ Configuration maintenance
- ✅ Context recovery
- ✅ Task verification

**Future enhancements:**

- Automatic task prioritization based on deadlines
- Integration with GitHub issues for cross-team visibility
- Analytics on task completion patterns
- Smart suggestions for next task based on history

Want to implement this in your workflow? The beads repository is at [github.com/steveyegge/beads](https://github.com/steveyegge/beads).

**The core lesson:** When AI agents lose context through compaction, persist your state in git. It's the one thing that survives everything.
