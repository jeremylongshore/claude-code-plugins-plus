---
name: cursor-git-integration
description: |
  Integrate Git workflows with Cursor IDE. Triggers on "cursor git",
  "git in cursor", "cursor version control", "cursor commit", "cursor branch".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Git Integration

## Built-in Git Features

### Source Control Panel
```
Access:
- Click Source Control icon in sidebar
- Cmd+Shift+G (Mac) / Ctrl+Shift+G (Windows)

Features:
- View changed files
- Stage/unstage changes
- View diffs
- Commit changes
- Push/pull
- Branch management
```

### Git Status Indicators
```
File explorer indicators:
M  = Modified (yellow)
A  = Added (green)
D  = Deleted (red)
U  = Untracked (gray)
C  = Conflict (red !)
R  = Renamed
```

## AI-Powered Git Workflows

### Generate Commit Messages
```
Method 1: Chat
Select changed files → Cmd+L →
"Generate a commit message for these changes"

Method 2: Source Control
1. Stage changes
2. Click sparkle icon in commit box
3. AI generates message

Method 3: Composer
"Review my staged changes and create a commit message"
```

### Code Review Assistance
```
Review changes before commit:
"@git diff HEAD Review these changes for issues"

Review specific commit:
"@git show abc123 Explain what this commit does"

Review branch:
"@git diff main..feature/auth Review all changes in this branch"
```

### Conflict Resolution
```
When conflicts occur:
1. Open conflicting file
2. See conflict markers:
   <<<<<<< HEAD
   your code
   =======
   their code
   >>>>>>> branch

3. Use AI to resolve:
   Select conflict → Cmd+L →
   "Resolve this conflict, keeping the new auth logic"

4. Or use inline edit:
   Cmd+K → "Merge keeping both implementations"
```

## Git Commands via Terminal

### Integrated Terminal
```bash
# Open terminal: Cmd+` or Ctrl+`

# Common operations
git status
git add .
git commit -m "message"
git push origin branch

# AI can help generate commands
Cmd+L: "How do I rebase my branch onto main?"
```

### Git Aliases for Cursor Workflow
```bash
# ~/.gitconfig
[alias]
    # Quick status
    s = status -sb

    # Commit with AI message (manual)
    cm = commit -m

    # Pretty log
    lg = log --oneline --graph --all

    # Undo last commit (keep changes)
    undo = reset HEAD~1 --soft

    # Amend without editing message
    amend = commit --amend --no-edit
```

## Branch Management

### Create Branch
```
Method 1: Status bar
Click branch name → Create new branch

Method 2: Command Palette
Cmd+Shift+P → "Git: Create Branch"

Method 3: Terminal
git checkout -b feature/new-feature
```

### Switch Branches
```
Method 1: Status bar (click branch name)
Method 2: Cmd+Shift+P → "Git: Checkout to"
Method 3: Terminal: git checkout branch-name
```

### Merge with AI Help
```
"Help me merge feature/auth into main:
- What conflicts might occur?
- How should I resolve them?
- What's the safest approach?"
```

## Viewing History

### Git Log
```
View in Cursor:
1. Source Control panel
2. Click "..." → "View History"

Or use terminal:
git log --oneline -20
git log --graph --all
```

### Blame/Annotate
```
Right-click in editor:
"Git: Show File History"
"Git: Show Line History"

Or via command palette:
"Git: Open File History"
```

### Diff Views
```
Compare working changes:
- Click file in Source Control
- Opens diff view

Compare branches:
Cmd+Shift+P → "Git: Compare..."

Compare commits:
Use terminal or GitLens extension
```

## Advanced Git Operations

### Interactive Rebase Help
```
Ask AI for guidance:
"I need to squash the last 5 commits. Walk me through:
1. The git commands
2. How to write a good combined message
3. How to handle force push safely"
```

### Cherry-Pick Guidance
```
"@git log Show recent commits on feature/payments"
"Help me cherry-pick commit abc123 to main:
- What's the command?
- How do I handle conflicts?
- Should I use -x flag?"
```

### Stash Operations
```
Stash with AI:
"I need to switch branches but have uncommitted changes.
Help me stash properly and restore later."

Commands:
git stash push -m "work in progress on auth"
git stash list
git stash pop
```

## Git Hooks Integration

### Pre-commit with Cursor
```bash
# .git/hooks/pre-commit
#!/bin/sh
npm run lint
npm run test

# Cursor works with existing hooks
# AI can help write hooks:
"Create a pre-commit hook that:
- Runs ESLint
- Checks for console.log
- Validates commit message format"
```

### Commit Message Templates
```bash
# .gitmessage template
# Type: feat|fix|docs|style|refactor|test|chore

# Subject (50 chars max)

# Body (72 chars per line)

# Footer (issues, breaking changes)

# Configure:
git config commit.template .gitmessage
```

## Best Practices

### Daily Workflow
```
Morning:
1. git pull (sync with remote)
2. Check for updates to main
3. Rebase if needed

During development:
1. Commit frequently (logical chunks)
2. Use AI for commit messages
3. Push regularly

End of day:
1. Push all commits
2. Create PR if ready
3. Update ticket/issue
```

### Commit Message Quality
```
AI prompt for good messages:
"Generate a commit message following conventional commits:
- Type: feat/fix/docs/refactor/test/chore
- Scope: (optional) affected module
- Subject: imperative, 50 chars
- Body: explain why, not what
- Footer: breaking changes, issues"
```

### Branch Hygiene
```
Keep branches clean:
- Delete merged branches
- Rebase over merge for feature branches
- Keep commits atomic and meaningful

AI help:
"Review my branch history. Should I squash any commits
before creating a PR?"
```

## Extensions for Enhanced Git

### GitLens
```
Recommended extension for:
- Inline blame
- Commit details
- File history
- Compare branches
- Heatmaps

Install: Extensions → Search "GitLens"
```

### Git Graph
```
Visual branch management:
- Interactive commit graph
- Branch/tag visualization
- Easy cherry-pick/rebase
```
