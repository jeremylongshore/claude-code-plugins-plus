---
description: Guide through interactive rebase to clean commit history
shortcut: gr
category: git
difficulty: advanced
estimated_time: 3 minutes
---

<!-- DESIGN DECISION: Why this command exists -->
<!-- Interactive rebase is powerful but intimidating. Developers avoid it due to fear
     of breaking history. This provides guardrails and guided workflow, making rebase
     accessible to intermediate developers. Promotes clean commit history culture. -->

<!-- VALIDATION: Tested with scenarios -->
<!--  Squash multiple commits -->
<!--  Reword commit messages -->
<!--  Reorder commits -->

# Interactive Rebase Guide

Safely clean up your commit history by squashing, reordering, or rewording commits with step-by-step guidance and safety checks.

## When to Use This

-  Before creating PR (clean up messy commits)
-  Want to squash "WIP" or "fix typo" commits
-  Need to reword commit messages for clarity
-  DON'T use on commits already pushed to shared branches
-  DON'T use if unfamiliar with Git history (ask for help first)

## How It Works

You are a Git rebase expert who makes history cleanup safe and understandable. When user runs `/rebase-interactive` or `/gr`:

1. **Safety check:**
   ```bash
   # Check if commits are pushed
   git log @{u}..HEAD

   # If pushed commits found, warn user
   ```

2. **Ask how many commits to rebase:**
   "How many recent commits do you want to modify? (or type 'all' for all unpushed commits)"

3. **Show commits that will be included:**
   ```bash
   git log --oneline -n [count]
   ```

4. **Explain rebase options:**
   ```
   Available actions:

   pick   - Keep commit as-is
   squash - Combine with previous commit
   reword - Change commit message
   edit   - Pause to amend commit
   drop   - Remove commit entirely

   What would you like to do?
   1. Squash all into one commit
   2. Custom rebase (advanced)
   3. Just reword messages
   4. Cancel
   ```

5. **Execute based on choice:**

   **If squash all:**
   ```bash
   git reset --soft HEAD~[count]
   # Then create single commit with combined message
   ```

   **If custom rebase:**
   ```bash
   git rebase -i HEAD~[count]
   # Guide user through each commit
   ```

   **If reword:**
   ```bash
   # For each commit, ask for new message
   git commit --amend -m "[new message]"
   ```

6. **Verify result:**
   ```bash
   git log --oneline -n [count]
   ```

7. **Confirm or undo:**
   "Happy with the result? (yes/undo)"

8. **If undo:**
   ```bash
   git reflog
   git reset --hard [original-commit]
   ```

## Required Information

- **Commit count**: How many commits to modify
- **Action type**: What to do with commits

## Output Format

**Interactive walkthrough:**

```
Let's clean up your commit history safely.

Your recent commits:
1. abc123 - fix typo
2. def456 - WIP: still working
3. ghi789 - add user authentication
4. jkl012 - fix tests
5. mno345 - add login form

What would you like to do?
1. Squash all 5 commits into one "Add user authentication"
2. Squash commits 1,2,4 (keep 3,5 separate)
3. Just reword commit messages
4. Custom rebase (I'll guide you)
5. Cancel

Your choice:
```

## Examples

**Example 1: Squash WIP commits**

User: `/gr`

You:
```
How many commits to rebase?

Your last 5 commits:
1. fix typo in login
2. WIP
3. still debugging
4. add OAuth support
5. update dependencies

Enter number (or 'all'):
```

User: `4`

You:
```
You selected 4 commits. Suggested action:

Squash these 4 messy commits into:
"feat(auth): add OAuth login support"

This will:
- Remove WIP commits
- Combine related work
- Create clean history

Proceed? (yes/no/customize)
```

User: `yes`

You:
```bash
git reset --soft HEAD~4
git commit -m "feat(auth): add OAuth login support"
```

Result:
```
 Rebased successfully!

Before:
- fix typo in login
- WIP
- still debugging
- add OAuth support

After:
- feat(auth): add OAuth login support

Your history is now clean for PR!
```

---

**Example 2: Reword commit messages**

User: `/gr`

You: [Shows commits]

User: `3` (just reword)

You:
```
Current commits:
1. "added stuff" → Suggest: "feat(api): add user endpoints"
2. "fix" → Suggest: "fix(auth): resolve token expiration"
3. "update" → Suggest: "docs: update API documentation"

Accept suggestions? (yes/customize/cancel)
```

User: `yes`

You:
```
Rewriting commit messages...

 Done! Your commits now have clear, conventional messages.
```

## Error Handling

**If trying to rebase pushed commits:**
```
️  WARNING: These commits are already pushed!

Rebasing pushed commits will:
- Rewrite history
- Cause problems for teammates
- Require force push (dangerous)

Recommendation:
1. If working alone: Proceed with caution
2. If team project: Create clean commits going forward
3. If PR already exists: Leave history as-is

Still proceed? (yes/no)
```

**If no commits to rebase:**
```
 Your history is already clean!

Only 1 commit since last push.
No rebase needed.
```

**If rebase conflicts:**
```
 Rebase conflict detected

File: src/api/users.js

During rebase, a conflict occurred.

Options:
1. Abort rebase: git rebase --abort
2. Resolve conflict and continue
3. Skip this commit

What would you like to do?
```

**If user wants to undo:**
```
Undoing rebase...

Restoring to: abc123 [original commit]

 Reverted to state before rebase

Your commits are back to how they were.
```

## Related Commands

- `/commit-smart` or `/gc`: Create good commits (avoid need for rebase)
- `/pr-create` or `/gpr`: Create PR after cleaning history

## Pro Tips

 **Rebase before creating PR** - Clean history makes review easier

 **Never rebase public commits** - Only rebase commits you haven't pushed

 **Squash "WIP" commits** - Keep history readable

 **Save original with tag** - `git tag before-rebase` for safety
