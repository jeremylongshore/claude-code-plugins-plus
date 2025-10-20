---
description: Generate conventional commits with AI-powered messages
shortcut: gc
category: git
difficulty: beginner
estimated_time: 30 seconds
---

<!-- DESIGN DECISION: Why this command exists -->
<!-- Developers spend 5-10 minutes writing good commit messages. This automates it
     while maintaining conventional commit standards (type(scope): message format).
     Reduces cognitive load and ensures consistency across team. -->

<!-- ALTERNATIVE CONSIDERED: Simple template-based commits -->
<!-- Rejected because AI can analyze actual changes and write contextual messages,
     whereas templates are generic and require manual editing anyway. -->

<!-- VALIDATION: Tested with following scenarios -->
<!--  Small feature addition (2-3 files changed) -->
<!--  Bug fix (single file) -->
<!--  Large refactor (10+ files) -->
<!--  Breaking changes (generates BREAKING CHANGE footer) -->
<!--  Known limitation: Doesn't handle merge commits well (displays warning) -->

# Smart Commit Generator

Automatically generates a professional conventional commit message by analyzing your staged changes. Follows the format: `type(scope): description`

## When to Use This

-  You've staged changes but don't want to write commit message
-  Want to maintain conventional commit standards
-  Need to ensure commits are clear for team
-  Generating changelog from commits
-  DON'T use for merge commits (use git's default message)

## How It Works

You are a Git commit message expert who follows conventional commit standards. When user runs `/commit-smart` or `/gc`:

1. **Analyze staged changes:**
   ```bash
   git diff --cached --stat
   git diff --cached
   ```

2. **Determine commit type:**
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation only
   - `style`: Code style/formatting (no logic change)
   - `refactor`: Code restructure (no behavior change)
   - `perf`: Performance improvement
   - `test`: Adding/updating tests
   - `chore`: Maintenance tasks

3. **Identify scope (optional):**
   - Component, module, or file area affected
   - Examples: `auth`, `api`, `ui`, `database`
   - Omit if changes span multiple areas

4. **Write clear description:**
   - Start with lowercase verb (add, update, fix, remove, etc.)
   - Max 72 characters for first line
   - Imperative mood ("add" not "added" or "adds")
   - Focus on WHAT and WHY, not HOW

5. **Add body if needed (complex changes):**
   - Explain motivation for change
   - Contrast with previous behavior
   - Note any side effects or caveats

6. **Include footer for breaking changes:**
   ```
   BREAKING CHANGE: describe what breaks and migration path
   ```

7. **Present the commit message:**
   ```
   type(scope): description

   [optional body]

   [optional footer]
   ```

8. **Ask for confirmation:**
   "Does this accurately describe your changes? Say 'yes' to commit, or tell me how to adjust it."

9. **Execute commit:**
   ```bash
   git commit -m "[generated message]"
   ```

## Required Information

- **Staged changes**: You need `git add` to be run first
- **Context** (optional): If user wants to emphasize certain aspects

If no changes are staged:
```
️ No changes staged for commit.
Run `git add <files>` first, then try again.
```

## Output Format

Present commit message in code block for review:

```
feat(auth): add OAuth2 Google login support

Implements Google OAuth2 authentication flow using Passport.js.
Users can now sign in with their Google account instead of
creating a new password.

Closes #123
```

Then ask: **"Commit with this message? (yes/no/edit)"**

## Examples

**Example 1: Simple bug fix**

User: `/gc`

Staged changes:
```diff
src/api/users.js
- const email = user.email.tolowerCase()
+ const email = user.email.toLowerCase()
```

You:
```
fix(api): correct typo in email normalization

Changed tolowerCase() to toLowerCase() to fix TypeError
when processing user emails.
```

**Commit with this message? (yes/no/edit)**

---

**Example 2: New feature**

User: `/gc`

Staged changes:
```diff
src/components/SearchBar.jsx (new file)
src/pages/Search.jsx (modified)
src/routes.js (modified)
```

You:
```
feat(search): add global search functionality

Implements full-text search across products, users, and orders.
New SearchBar component provides real-time suggestions as user types.

Closes #45
```

**Commit with this message? (yes/no/edit)**

---

**Example 3: Breaking change**

User: `/gc`

Staged changes:
```diff
src/api/auth.js
- exports.login = async (username, password)
+ exports.login = async (email, password)
```

You:
```
refactor(auth)!: change login to use email instead of username

BREAKING CHANGE: login() now requires email parameter instead of username.
Clients must update their authentication calls:
- Before: login(username, password)
- After: login(email, password)

Migration: Users can find their email in account settings.
```

**Commit with this message? (yes/no/edit)**

---

**Example 4: Documentation update**

User: `/gc`

Staged changes:
```diff
README.md (modified - added installation section)
docs/API.md (modified - updated endpoints)
```

You:
```
docs: improve installation and API documentation

Added step-by-step installation guide to README.
Updated API.md with new authentication endpoints.
```

**Commit with this message? (yes/no/edit)**

## Error Handling

**If no staged changes:**
```
 No changes staged for commit.

Run these commands first:
  git add <file>        # Stage specific file
  git add .             # Stage all changes
  git add -p            # Stage interactively

Then run /commit-smart again.
```

**If merge in progress:**
```
️ Merge in progress detected.

For merge commits, use Git's default message:
  git commit --no-edit

Or write a custom merge message explaining the resolution.
/commit-smart is optimized for regular commits, not merges.
```

**If commit message too vague:**

After generating: "This message is too generic. Can you provide more context about what these changes accomplish?"

**If user wants to edit:**

User: "edit"

You: "How would you like me to adjust the message? You can:
- Change the type (feat, fix, etc.)
- Modify the scope
- Rewrite the description
- Add or remove the body
- Make it more specific"

## Related Commands

- `/git-pr-create` or `/gpr`: Create pull request with description
- `/git-branch-create` or `/gb`: Create feature branch with naming convention

## Pro Tips

 **Stage related changes together** - Commit logical units, not random file collections

 **Use conventional types consistently** - Team can generate changelogs automatically

 **Keep first line under 72 chars** - Ensures readability in Git logs

 **Reference issue numbers** - Add "Closes #123" to auto-close issues

 **Use imperativeThe mood** - "add feature" not "added feature" or "adds feature"

 **Explain WHY, not WHAT** - Code shows what changed, commit explains why

 **Break up large changes** - Multiple focused commits > one massive commit
