<!-- markdownlint-disable MD024 -->

# Agent Instructions

<!-- bd-doctor-divergence: ok -->
<!-- AGENTS.md and CLAUDE.md are intentionally distinct in this repo.
     CLAUDE.md = repository-specific guidance (build commands, conventions, marketplace layout).
     AGENTS.md = generic agent / beads session protocol.
     CLAUDE.md explicitly delegates session protocol here ("Session protocol lives in AGENTS.md"). -->

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

---

## 🚨 MANDATORY: Session Continuation Protocol

**CRITICAL**: When this session continues after context compaction/summarization:

**YOU MUST IMMEDIATELY RUN**:

```bash
bd ready
```

**WHY**: After context loss, beads is your ONLY source of truth for:

- What tasks are in progress
- What was being worked on before context compaction
- What's blocked/ready to work on
- Project status and next steps

**THIS IS NON-NEGOTIABLE**: Do NOT proceed with ANY work until you've run `bd ready`.

**Failure to read beads after context compaction = working blind = wasted effort**

---

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:

   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```

5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**

- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

---

## Before You Touch Validators, Schemas, or the Kernel Pin

This repo is mid-migration toward a single source of truth for "what is a valid agent-native artifact." An agent working here must know the following before changing anything under `scripts/validate-*`, `package.json`'s kernel pin, or the schema docs.

**The authoritative gate is `scripts/validate-skills-schema.py`.** It is the one in the branch-protection required-status set. At marketplace tier, a missing required field is an **ERROR, not a warning**. The IS 8-field `ALWAYS_REQUIRED` set is hand-authored and stays **AUTHORITATIVE**. The IS rubric sits on top of Anthropic's permissive spec — do not reduce the 8-field set, do not demote marketplace errors to warnings, do not "realign" to Anthropic's floor. Read `000-docs/SCHEMA_CHANGELOG.md` § NON-NEGOTIABLES first; any change to required-fields / tier model / error-vs-warning semantics is approval-gated there.

**The kernel `@intentsolutions/core` (`schemas/authoring/v1` byte-frozen + `authoring/v2` strict fork) is the SSoT.** The validator is migrating to consume the kernel folds instead of its hand-rolled rule sets — that work is in progress and the advisory→authoritative flip has **not** happened.

**Pin tracks the latest published kernel — exactly `0.9.0` (no `^`/`~`).** The `authoring/v1` family is byte-frozen across kernel versions, so the pin bump is a governance/coupling update, not an authority change. Keep it EXACT (no `^`/`~`); bump it deliberately when the kernel publishes a new latest, in a dedicated coupling PR. The advisory→authoritative flip is a SEPARATE, gated step — bumping the pin must never flip it.

**Two advisory CI lanes — they never block:**

- `kernel-shadow-validation.yml` (DR-049 shadow soak) runs the kernel-pinned schema over the SKILL.md corpus and logs AGREE/DISAGREE to `scripts/.kernel-shadow/report.json`.
- `kernel-vendor-hash.yml` enforces the V ≤ C ≤ K version-coupling invariant + a ≤7-day staleness bound.

Both are `continue-on-error: true`, are not required checks, and mutate nothing. Do not treat their output as a merge blocker, and do not "fix" them by bumping the pin.

**Do NOT flip the shadow lane to blocking** until ALL hold: ≥99.5% corpus agreement (deterministic folds = 100%; the 0.5% band is non-deterministic surfaces only), ≥30 days of advisory soak, zero open P0 blockers, the Rekor superseding-event rollback protocol implemented and tested, CTO + CISO + VP-DevRel governance sign-off, and a ≥14-day public deprecation-window notice to affected authors. The soak has not met this bar yet — the open disagreements are real tool-safety / shell-substitution security cases the current validator correctly blocks. Promotion to blocking is a separate, later, condition-gated step, never a side effect of an unrelated change.

**`[skip auto-bump]` for non-release PRs.** `auto-bump-on-pr.yml` auto-bumps changed plugins' patch versions (only on `plugins/**` / `packages/**` changes). For a docs-only or non-release PR, put `[skip auto-bump]` in the PR title or body so the auto-bumper steps aside.

---

<!-- BEGIN BEADS INTEGRATION -->

## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Dolt-powered version control with native sync
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update <id> --claim --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task atomically**: `bd update <id> --claim`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs via Dolt:

- Each write auto-commits to Dolt history
- Use `bd dolt push`/`bd dolt pull` for remote sync
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:

   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```

5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**

- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

<!-- END BEADS INTEGRATION -->
