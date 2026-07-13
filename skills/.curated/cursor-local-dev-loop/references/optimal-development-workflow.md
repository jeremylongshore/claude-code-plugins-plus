# Optimal Development Workflow

## Optimal Development Workflow

### Morning Startup

```bash
# 1. Open project
cursor /path/to/project

# 2. Let indexing complete (check status bar)
# 3. Review yesterday's changes
git diff HEAD~1

# 4. Check AI chat for context
# Cmd+L: "Summarize recent changes in this codebase"
```

### Feature Development Cycle

```
┌─────────────────────────────────────────┐
│  1. Define Task (Chat)                  │
│     Cmd+L: "I need to add user auth"    │
├─────────────────────────────────────────┤
│  2. Generate Scaffold (Composer)        │
│     Cmd+I: "Create auth module with..." │
├─────────────────────────────────────────┤
│  3. Iterate with Tab Completion         │
│     Write code, accept AI suggestions   │
├─────────────────────────────────────────┤
│  4. Debug with Chat                     │
│     Select error, Cmd+L: "Why fails?"   │
├─────────────────────────────────────────┤
│  5. Refactor with Inline Edit           │
│     Select code, Cmd+K: "Optimize"      │
└─────────────────────────────────────────┘
```
