# Git Hooks Integration

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
