# Git Commands Via Terminal

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
