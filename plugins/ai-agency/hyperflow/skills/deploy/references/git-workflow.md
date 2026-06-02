# Git Workflow

Automated git operations integrated into the orchestrator cycle. Auto-commit is on by default.

## Flow

```
Session starts
    |
[Opus] On a feature branch? 
    |-- Yes -> continue
    |-- No -> create branch (feat/task-description)
    |
... workers execute tasks ...
    |
[Opus] Task approved by reviewer + quality gates pass
    |
[Opus] Auto-commit? 
    |-- On (default) -> commit with descriptive message
    |-- Off -> stage changes, skip commit
    |
... all tasks done ...
    |
[Opus] Final review passes
    |
[Opus] Ask: squash into one commit or keep individual?
```

## Rules

1. **Never commit to main/master directly.** Create a feature branch first. Branch naming: `feat/<short-description>`, `fix/<short-description>`, `refactor/<short-description>`.
2. **Commit per sub-task, not per batch.** Every sub-task that the dispatch phase reviews and approves produces its own commit. A batch of 3 parallel sub-tasks produces 3 commits, not 1. This keeps history bisectable, makes reverts surgical, and prevents an unrelated regression from being co-mingled with an unrelated change.
3. **Commit immediately after the per-sub-task reviewer returns `PASS`.** Order within a batch: worker writes → thinking-tier reviewer approves → commit that sub-task's files only → move on. Quality gates run once at the end of the batch over the cumulative state; if gates fail, fix-commits sit on top (don't amend earlier per-task commits).
4. **Follow project commit conventions.** Read CLAUDE.md / commitlint config for message format. Default to conventional commits (`feat:`, `fix:`, `refactor:`, etc.) — type chosen from the sub-task's nature.
5. **No LLM attribution anywhere in the artefact.** Never add "Co-Authored-By: Claude" (or any LLM trailer). Never reference "Claude" / "AI" / "assistant" / "the LLM" as a subject performing an action in commit messages, PR descriptions, rebase notes, code comments, doc prose, or skill bodies. Describe what changed, not who made it. Product names used as named tools (`claude` CLI, `Claude Code` platform, `CLAUDE.md` filename) are fine — banned use is only as a *narrative subject*. See DOCTRINE rule 9 for the full statement.
6. **Stage only the files this sub-task touched.** Use `git add <specific-files>` — never `git add -A` or `git add .`. The Planner's per-sub-task file list (from `/hyperflow:scope`) IS the staging list.
7. **Don't push automatically.** Commit locally. Push is gated by an explicit `AskUserQuestion` in `/hyperflow:deploy` Step 6.

## Auto-Commit Toggle

**On (default):** After each approved task, Opus commits with a descriptive message.

**Off:** Opus stages changes but does not commit. User commits manually.

### How to disable

Any of these work:

- In CLAUDE.md: `hyperflow: auto-commit off`
- In conversation: "don't auto-commit" or "hyperflow: auto-commit off"
- Per-task: "do this but don't commit"

### How to re-enable

- In conversation: "hyperflow: auto-commit on"
- Removing the CLAUDE.md line

## Commit Message Format

The thinking-tier orchestrator generates the commit message for each sub-task immediately after its reviewer returns `PASS`. Inputs to the message:

1. Project conventions (CLAUDE.md, commitlint config)
2. What the worker actually changed (the diff)
3. The sub-task title + description from the task file (`.hyperflow/tasks/<slug>.md`)
4. The persona stitching for that sub-task (e.g. `[security + api]` ⇒ likely `feat(auth):` or `feat(api):`)

```
feat(auth): add JWT middleware with RS256 verification

Implements auth middleware that validates JWT tokens using RS256.
Includes rate limiting and session refresh logic.
```

Aim for **one logical change per commit**. If a sub-task touched more than one logical concern (rare — usually a scope/planner mistake), split into multiple commits *within* the per-sub-task slot.

## Branch Strategy

| Task type | Branch prefix | Example |
|-----------|--------------|---------|
| New feature | `feat/` | `feat/user-auth` |
| Bug fix | `fix/` | `fix/login-redirect` |
| Refactor | `refactor/` | `refactor/extract-validation` |
| Chore | `chore/` | `chore/update-deps` |

## End of Dispatch (per-task commits already on the branch)

By the time `/hyperflow:dispatch` reaches Step 5 (End of chain), every approved sub-task is already its own commit. There is no end-of-session "wrap-up commit" — only the per-task commits made along the way, plus any small fix-commits that landed because a quality gate caught something.

The dispatch skill then asks the user **two separate questions** before stopping:

1. **Run `/hyperflow:audit` on the changes?** — `AskUserQuestion`, recommended `Yes` for deep / scientific flow profiles, recommended `No` for fast / standard profiles (the per-batch reviewers already covered L1–L2). Audit gives an outside-eye L3 review on the cumulative diff before the user even thinks about pushing.
2. **Run `/hyperflow:deploy` (full gates + commit + push)?** — `AskUserQuestion`. Deploy is independent from the dispatch chain and asks its own push-confirmation gate at Step 6. Recommended `Yes` when all dispatch gates were green; recommended `No` if the user wants to inspect the diff manually first.

The orchestrator does **NOT** auto-invoke either skill. Both run only on the user's explicit yes.

If you want to keep working in the branch instead, both questions accept `No / not now / stop` and dispatch just stops cleanly with the per-task commits in place.

## Squashing (optional, manual)

If you prefer one commit per feature instead of per-task on the published branch, squash manually before opening the PR:

```bash
git rebase -i origin/main   # mark per-task commits as `squash` / `fixup`
```

Hyperflow does not squash automatically — surgical history is the default, not a flat blob.


## Conflict Handling

If a commit fails due to conflicts:
1. Opus identifies the conflicting files
2. Dispatches a Sonnet worker to resolve conflicts
3. Opus reviews the resolution
4. Commits the merge resolution
