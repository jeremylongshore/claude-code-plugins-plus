# Performance Pitfalls

## Performance Pitfalls

### Too Many Extensions

```
PITFALL:
Installing every interesting extension.
Slow startup, memory issues.

SOLUTION:
- Audit extensions regularly
- Disable unused extensions
- Use workspace-specific extensions
- Remove completely if not needed
```

### Large Context Requests

```
PITFALL:
@-mentioning entire folders.
Slow responses, context overflow.

SOLUTION:
- @-mention specific files
- Select only relevant code
- Use focused queries
- Start new chat when bloated
```

### Indexing Entire Codebase

```
PITFALL:
Indexing massive monorepo.
Never-ending indexing, high CPU.

SOLUTION:
- Aggressive .cursorignore
- Open specific packages
- Use workspace folders
- Manual indexing for large projects
```
