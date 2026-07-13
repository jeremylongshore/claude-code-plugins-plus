# Best Practices

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
