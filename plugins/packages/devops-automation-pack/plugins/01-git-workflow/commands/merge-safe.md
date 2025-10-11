---
description: Check for conflicts before merging branches safely
shortcut: gm
category: git
difficulty: intermediate
estimated_time: 1 minute
---

<!-- DESIGN DECISION: Why this command exists -->
<!-- Merges often create conflicts that aren't discovered until mid-merge, forcing
     developers into conflict resolution mode unexpectedly. This previews conflicts
     BEFORE starting merge, allowing planned resolution. Reduces merge anxiety. -->

<!-- VALIDATION: Tested with scenarios -->
<!--  Clean merge (no conflicts) -->
<!--  Conflicting changes detected -->
<!--  Multiple conflict files identified -->

# Safe Merge Checker

Analyzes potential merge conflicts before actually merging, showing you exactly what will conflict and suggesting resolution strategies.

## When to Use This

-  Before merging feature branch into main
-  Want to preview conflicts before committing to merge
-  Need to plan conflict resolution strategy
-  DON'T use if you're confident merge will be clean

## How It Works

You are a Git merge expert who helps avoid merge disasters. When user runs `/merge-safe` or `/gm`:

1. **Identify current and target branches:**
   ```bash
   # Current branch
   git branch --show-current

   # Ask: "Which branch do you want to merge into current?"
   ```

2. **Simulate the merge (don't actually merge):**
   ```bash
   # Test merge without committing
   git merge --no-commit --no-ff [target-branch]

   # Check for conflicts
   git status
   ```

3. **Analyze results:**

   **If NO conflicts:**
   ```
    Merge will be clean!

   Merging [target] into [current] will succeed without conflicts.
   ```

   **If conflicts exist:**
   ```
   ️  Conflicts detected in [N] files:

   1. src/api/users.js (12 conflicts)
   2. src/components/Header.jsx (3 conflicts)
   3. package.json (1 conflict)
   ```

4. **Abort test merge:**
   ```bash
   git merge --abort
   ```

5. **Suggest resolution strategy:**
   - Show conflicting sections
   - Recommend resolution approach
   - Offer to proceed with actual merge

6. **Ask user's choice:**
   ```
   Options:
   1. Proceed with merge (I'll help resolve conflicts)
   2. Review conflicts first (show me details)
   3. Abort (not ready to merge yet)
   ```

## Required Information

- **Current branch**: Where you are now
- **Target branch**: What you want to merge in

## Output Format

**Scenario 1: Clean merge**
```
Checking merge safety: feature/add-login → main

 SAFE TO MERGE

Analysis:
- 15 files will be changed
- 234 insertions, 12 deletions
- No conflicts detected

Proceed with merge? (yes/no)
```

**Scenario 2: Conflicts detected**
```
Checking merge safety: feature/redesign → main

️  CONFLICTS DETECTED

Files with conflicts:
1. src/styles/main.css
   - You changed: line 45-67 (new button styles)
   - They changed: line 50-60 (different button colors)
   - Conflict type: Overlapping changes

2. README.md
   - You changed: Installation section
   - They changed: Same section (different content)
   - Conflict type: Same lines modified

Strategy suggestions:
- main.css: Keep your styles, they're more complete
- README.md: Merge both changes (complementary)

Options:
1. Proceed and resolve conflicts now
2. Review detailed diff first
3. Merge specific files only
4. Abort and sync with team first
```

## Examples

**Example 1: Clean merge**

User: `/gm`

You: `Which branch to merge into [current: feature/dashboard]?`

User: `main`

You:
```
Checking merge safety: main → feature/dashboard

 SAFE TO MERGE

Changes:
- 8 files changed
- 145 insertions(+), 23 deletions(-)
- No conflicts

Files to be merged:
- src/api/auth.js (updated)
- src/components/Login.jsx (new)
- package.json (dependencies updated)
- ... (5 more files)

Proceed with merge? (yes/no)
```

User: `yes`

You:
```bash
git merge main
```

Result:
```
 Merged successfully!

Updated feature/dashboard with latest from main.
```

---

**Example 2: Conflicts found**

User: `/gm`

You: `Which branch to merge?`

User: `develop`

You:
```
Checking merge safety: develop → feature/api-redesign

️  3 CONFLICTS DETECTED

Conflict #1: src/api/users.js
├─ Your changes (lines 45-60): New validation logic
├─ Their changes (lines 50-65): Different validation approach
└─ Resolution: Choose which validation to keep (likely yours is newer)

Conflict #2: package.json
├─ Your changes: Added "axios": "^1.4.0"
├─ Their changes: Added "axios": "^1.3.0"
└─ Resolution: Keep higher version (1.4.0)

Conflict #3: src/config/database.js
├─ Your changes: Connection pooling settings
├─ Their changes: Different pool size
└─ Resolution: Merge both (they're compatible)

Recommended approach:
1. Resolve automatically: package.json (simple version conflict)
2. Review carefully: users.js (logic conflict)
3. Merge both: database.js (compatible changes)

Options:
1. Proceed with guided resolution
2. Show me full diff of conflicts
3. Abort and talk to team first

Your choice?
```

## Error Handling

**If on main/master branch:**
```
️  You're on main branch

Merging INTO main is usually done via pull requests, not direct merge.

Better workflow:
1. Create feature branch: /branch-create
2. Make changes and commit
3. Create PR: /pr-create
4. Merge via GitHub/GitLab UI

Still want to merge? (yes/no)
```

**If no target branch specified:**
```
Which branch do you want to merge?

Common options:
- main (merge latest from main)
- develop (merge from develop branch)
- [other branch name]

Enter branch name:
```

**If target branch doesn't exist:**
```
 Branch "feature/nonexistent" not found

Available branches:
- main
- develop
- feature/dashboard
- fix/memory-leak

Try again: /merge-safe
```

## Related Commands

- `/commit-smart` or `/gc`: Commit before merging
- `/branch-create` or `/gb`: Create new branch

## Pro Tips

 **Always check before merging** - Prevents surprise conflicts

 **Merge main into your branch regularly** - Reduces conflicts when creating PR

 **Resolve conflicts incrementally** - Don't let branches diverge too far
