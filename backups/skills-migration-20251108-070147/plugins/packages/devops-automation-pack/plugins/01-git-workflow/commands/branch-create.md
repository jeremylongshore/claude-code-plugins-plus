---
description: Create feature branch with team naming convention
shortcut: gb
category: git
difficulty: beginner
estimated_time: 20 seconds
---

<!-- DESIGN DECISION: Why this command exists -->
<!-- Teams enforce branch naming conventions (feature/, fix/, etc.) but developers
     often forget or use inconsistent names. This ensures compliance and includes
     issue number automatically. Prevents PR rejection due to branch naming. -->

<!-- ALTERNATIVE CONSIDERED: Git hooks for branch naming -->
<!-- Rejected because hooks are local config (not portable) and punitive (blocks after mistake).
     This is proactive (prevents mistake) and user-friendly (suggests correct format). -->

<!-- VALIDATION: Tested with scenarios -->
<!--  Feature branch creation -->
<!--  Fix branch creation -->
<!--  Hotfix branch creation -->

# Branch Creator

Creates a new Git branch following your team's naming convention (feature/*, fix/*, etc.) with optional issue number integration.

## When to Use This

-  Starting new feature or bugfix work
-  Want consistent branch naming across team
-  Need to reference issue/ticket number in branch
-  DON'T use for one-off experiments (use regular git checkout)

## How It Works

You are a Git branch naming expert who enforces team conventions. When user runs `/branch-create` or `/gb`:

1. **Ask for branch type:**
   ```
   What type of branch?
   1. feature - New functionality
   2. fix - Bug fix
   3. hotfix - Production bug fix
   4. refactor - Code restructuring
   5. docs - Documentation updates
   6. test - Test improvements
   ```

2. **Ask for description:**
   "Brief description (2-4 words, will be kebab-cased):"

3. **Ask for issue number (optional):**
   "Issue/ticket number (optional, press Enter to skip):"

4. **Generate branch name:**
   Format: `[type]/[issue]-[description]` or `[type]/[description]`

   Examples:
   - `feature/123-add-oauth`
   - `fix/456-memory-leak`
   - `feature/user-dashboard`

5. **Verify branch doesn't exist:**
   ```bash
   git branch --list [branch-name]
   ```

6. **Create and checkout branch:**
   ```bash
   git checkout -b [branch-name]
   ```

7. **Confirm creation:**
   ```
    Created and switched to branch: [branch-name]

   Next steps:
   - Make your changes
   - git add .
   - /commit-smart
   - /pr-create
   ```

## Required Information

- **Branch type**: One of the standard types (feature, fix, etc.)
- **Description**: Brief description of the work (2-4 words)
- **Issue number** (optional): Ticket/issue reference

## Output Format

Interactive prompts followed by confirmation:

```
What type of branch?
1. feature
2. fix
3. hotfix

> feature

Brief description (2-4 words):
> add OAuth login

Issue number (optional):
> 123

 Created and switched to branch: feature/123-add-oauth

Next steps:
- Make your changes
- /commit-smart (when ready to commit)
- /pr-create (when ready for review)
```

## Examples

**Example 1: Feature with issue number**

User: `/gb`

You:
```
What type of branch?
1. feature - New functionality
2. fix - Bug fix
3. hotfix - Production bug fix
```

User: `1` or `feature`

You: `Brief description (2-4 words):`

User: `add user dashboard`

You: `Issue number (optional):`

User: `45`

You:
```
 Created and switched to branch: feature/45-add-user-dashboard

Next steps:
- Make your changes
- /commit-smart
- /pr-create
```

---

**Example 2: Bugfix without issue**

User: `/gb`

You: [Shows branch type menu]

User: `fix`

You: `Brief description:`

User: `memory leak`

You: `Issue number (optional):`

User: [presses Enter]

You:
```
 Created and switched to branch: fix/memory-leak

Next steps:
- Make your changes
- /commit-smart
- /pr-create
```

---

**Example 3: Hotfix (urgent production fix)**

User: `/gb`

You: [Shows menu]

User: `hotfix`

You: `Brief description:`

User: `payment gateway timeout`

You: `Issue number (optional):`

User: `999`

You:
```
 Created and switched to branch: hotfix/999-payment-gateway-timeout

️  Hotfix detected - Remember to:
1. Fix the issue
2. Test thoroughly
3. Create PR to main AND develop branches
4. Deploy immediately after approval
```

## Error Handling

**If branch already exists:**
```
 Branch already exists: feature/45-add-dashboard

Options:
1. Switch to existing branch: git checkout feature/45-add-dashboard
2. Choose different name: /branch-create
3. Delete old branch first: git branch -d feature/45-add-dashboard
```

**If uncommitted changes exist:**
```
️ You have uncommitted changes

Options:
1. Commit them first: /commit-smart
2. Stash them: git stash
3. Discard them: git reset --hard (️ destructive!)

Then run /branch-create again
```

**If not in git repository:**
```
 Not in a git repository

Initialize git first:
  git init
  git add .
  git commit -m "Initial commit"

Then: /branch-create
```

**If description too long:**
```
️ Description too long: "add-complete-user-authentication-system"

Keep it concise (2-4 words):
 "add-user-auth"
 "user-authentication"

Try again: /branch-create
```

## Related Commands

- `/commit-smart` or `/gc`: Commit changes on this branch
- `/pr-create` or `/gpr`: Create PR when ready

## Pro Tips

 **Use issue numbers** - Makes tracking easier and links branch to ticket

 **Keep descriptions short** - Long branch names are hard to type and read

 **Follow team convention** - If your team uses different prefixes, adapt the format
