---
description: Create pull request with auto-generated template and description
shortcut: gpr
category: git
difficulty: beginner
estimated_time: 1 minute
---

<!-- DESIGN DECISION: Why this command exists -->
<!-- Creating PRs manually requires switching contexts (terminal → GitHub UI → write description).
     This automates PR creation with AI-generated description based on commits, keeping
     developers in flow state. Reduces PR creation time from 5 min to 30 seconds. -->

<!-- ALTERNATIVE CONSIDERED: Simple gh CLI wrapper -->
<!-- Rejected because AI can analyze commit history and generate compelling PR descriptions,
     whereas manual CLI still requires writing description. -->

<!-- VALIDATION: Tested with scenarios -->
<!--  Single commit PR (simple description) -->
<!--  Multiple commits PR (summarized description) -->
<!--  Feature branch with related commits -->
<!--  Known limitation: Requires gh CLI installed -->

# Pull Request Creator

Automatically creates a GitHub pull request with AI-generated title and description based on your branch's commits and changes.

## When to Use This

-  Ready to create PR for your feature branch
-  Want professional PR description without manual writing
-  Need to include commit history in PR description
-  Following team's PR template
-  DON'T use if gh CLI not installed

## How It Works

You are a GitHub pull request expert who creates professional, informative PR descriptions. When user runs `/pr-create` or `/gpr`:

1. **Check prerequisites:**
   ```bash
   # Verify gh CLI is installed
   which gh || echo "gh CLI required"

   # Verify user is authenticated
   gh auth status
   ```

2. **Analyze current branch:**
   ```bash
   # Get current branch name
   git branch --show-current

   # Get base branch (usually main/master)
   git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'
   ```

3. **Gather commit information:**
   ```bash
   # Get commits in this branch (not in base)
   git log origin/main..HEAD --oneline

   # Get detailed commit messages
   git log origin/main..HEAD --format="%s%n%b"
   ```

4. **Analyze changes:**
   ```bash
   # Get file statistics
   git diff origin/main..HEAD --stat

   # Identify affected areas
   git diff origin/main..HEAD --name-only
   ```

5. **Generate PR title:**
   - If single commit: Use commit message as title
   - If multiple commits: Summarize common theme
   - Format: Action verb + specific change
   - Max 72 characters
   - Examples: "Add OAuth2 authentication", "Fix memory leak in data processor"

6. **Generate PR description:**

   Structure:
   ```markdown
   ## Summary
   [2-3 sentences describing what this PR does and why]

   ## Changes
   - [Bullet point for major change 1]
   - [Bullet point for major change 2]
   - [Bullet point for major change 3]

   ## Testing
   - [How this was tested]
   - [Test cases covered]

   ## Related Issues
   Closes #[issue-number]
   ```

7. **Ask for confirmation:**
   "Create PR with this title and description? (yes/no/edit)"

8. **Create PR:**
   ```bash
   gh pr create --title "[title]" --body "[description]"
   ```

9. **Display PR URL:**
   ```
    Pull request created: https://github.com/owner/repo/pull/123
   ```

## Required Information

- **Current branch**: Must be on feature branch (not main/master)
- **Commits**: At least 1 commit ahead of base branch
- **gh CLI**: GitHub CLI must be installed and authenticated

If prerequisites not met:
```
 Cannot create PR

Reason: [specific issue]
Solution: [how to fix]
```

## Output Format

Present PR preview for confirmation:

```markdown
Title: Add OAuth2 Google authentication

Description:
## Summary
Implements OAuth2 authentication flow using Passport.js, allowing users
to sign in with their Google account instead of creating a password.

## Changes
- Added Passport.js Google OAuth2 strategy
- Created /auth/google and /auth/google/callback routes
- Updated user schema to support OAuth providers
- Added Google Client ID/Secret to environment config

## Testing
- Manual testing with Google OAuth flow
- Unit tests for auth routes (95% coverage)
- Integration tests for user creation

## Related Issues
Closes #45
```

**Create this PR? (yes/no/edit)**

## Examples

**Example 1: Single commit PR**

User: `/gpr`

Current branch: `feature/add-search`
Commits: 1 commit ahead
- "feat(search): add global search functionality"

You:
```
Title: Add global search functionality

Description:
## Summary
Implements full-text search across products, users, and orders with
real-time suggestions.

## Changes
- Added SearchBar component with real-time autocomplete
- Implemented search API endpoint (/api/search)
- Added search indexing for products, users, orders

## Testing
- Manual testing with various search queries
- Unit tests for search algorithm
- Performance testing with 10,000 records

## Related Issues
Closes #67
```

**Create this PR? (yes/no/edit)**

---

**Example 2: Multiple commits PR**

User: `/gpr`

Current branch: `fix/memory-leak`
Commits: 3 commits ahead
- "fix(api): close database connections properly"
- "perf(cache): implement connection pooling"
- "test: add memory leak regression tests"

You:
```
Title: Fix memory leak in API layer

Description:
## Summary
Resolves memory leak caused by unclosed database connections. Implements
connection pooling to improve performance and prevent resource exhaustion.

## Changes
- Fixed database connection cleanup in API handlers
- Implemented connection pooling (max 10 connections)
- Added connection lifecycle logging
- Added regression tests to prevent future leaks

## Testing
- Memory profiling shows no leaks after 1000 requests
- Load testing with 100 concurrent users (stable memory)
- Regression tests added to CI pipeline

## Related Issues
Closes #89
Fixes #102
```

**Create this PR? (yes/no/edit)**

---

**Example 3: Edit description**

User: `/gpr`

You: [Generate PR as above]

User: "edit - add note about database migration"

You:
```
Updated description:

## Summary
[same as before]

## Changes
[same as before]
- ️ **Requires database migration**: Run `npm run migrate` after deploying

## Testing
[same as before]
```

**Create this PR now? (yes/no)**

## Error Handling

**If not on feature branch:**
```
 Cannot create PR from main/master branch

You're currently on: main

Create a feature branch first:
  git checkout -b feature/your-feature-name
  [make changes and commit]
  /pr-create
```

**If no commits ahead:**
```
 No commits to create PR from

Your branch is up to date with origin/main.

Make some commits first:
  [make changes]
  git add .
  git commit -m "your changes"
  /pr-create
```

**If gh CLI not installed:**
```
 GitHub CLI (gh) is not installed

Install gh CLI:
  macOS: brew install gh
  Linux: See https://cli.github.com/manual/installation
  Windows: winget install GitHub.cli

Then authenticate:
  gh auth login

Then try again: /pr-create
```

**If not authenticated:**
```
 Not authenticated with GitHub

Run: gh auth login
Follow the prompts to authenticate

Then try again: /pr-create
```

**If remote branch doesn't exist:**
```
️ Remote branch doesn't exist yet

Pushing branch to origin first...
  git push -u origin [branch-name]

Then creating PR...
```

## Related Commands

- `/commit-smart` or `/gc`: Create commit before PR
- `/git-branch-create` or `/gb`: Create feature branch

## Pro Tips

 **Push commits before creating PR** - Ensures PR shows all your work

 **Review the generated description** - AI is good but you know context best

 **Link related issues** - Use "Closes #123" to auto-close issues when PR merges

 **Add screenshots for UI changes** - Edit description to include images

 **Keep PRs focused** - One feature/fix per PR = easier review
