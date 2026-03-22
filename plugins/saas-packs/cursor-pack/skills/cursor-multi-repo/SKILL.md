---
name: "cursor-multi-repo"
description: |
  Work with multiple repositories in Cursor: multi-root workspaces, monorepo patterns, selective indexing,
  and cross-project context. Triggers on "cursor multi repo", "cursor multiple projects", "cursor monorepo",
  "cursor workspace", "multi-root workspace".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
tags: [saas, cursor, cursor-multi]

---
# Cursor Multi-Repo

Work with multiple repositories and monorepo structures in Cursor. Covers multi-root workspaces, selective indexing, cross-project context, and rule inheritance patterns.

## Multi-Root Workspaces

Open multiple project roots in a single Cursor window:

### Creating a Workspace

1. Open first project: `File` > `Open Folder` > select project A
2. Add second project: `File` > `Add Folder to Workspace...` > select project B
3. Save workspace: `File` > `Save Workspace As...` > `mywork.code-workspace`

### Workspace File Structure

```json
// mywork.code-workspace
{
  "folders": [
    { "path": "/home/dev/api-service" },
    { "path": "/home/dev/web-frontend" },
    { "path": "/home/dev/shared-lib" }
  ],
  "settings": {
    "editor.tabSize": 2,
    "files.exclude": {
      "**/node_modules": true,
      "**/dist": true
    }
  }
}
```

Open workspace: `cursor mywork.code-workspace` or double-click the file.

### How Indexing Works with Multi-Root

- Each folder root is indexed independently
- `@Codebase` searches across all open roots
- `@Files` paths include the root name: `@api-service/src/routes/users.ts`
- Closing a folder removes it from the index

## Monorepo Patterns

### Opening Full Monorepo

```bash
cursor /path/to/monorepo
```

**Pros:** `@Codebase` searches everything, cross-package references work naturally
**Cons:** Slow indexing on large monorepos, lots of irrelevant search results

### Focused Opening (Recommended)

```bash
# Open just the package you're working on
cursor /path/to/monorepo/packages/api
```

**Pros:** Fast indexing, focused search results
**Cons:** No automatic cross-package context

### Hybrid: Focused + Selective .cursorignore

```bash
# Open the monorepo root but exclude what you don't need
cursor /path/to/monorepo
```

```gitignore
# .cursorignore at monorepo root
# Only index packages you're actively working on

# Exclude everything in packages/
packages/*/

# Except the ones you want indexed:
!packages/api/
!packages/shared/

# Always exclude
node_modules/
dist/
build/
.turbo/
```

This indexes only `packages/api/` and `packages/shared/`, keeping search focused.

## Cross-Project Context

### Referencing Files Across Roots

In a multi-root workspace, use the root folder name as prefix:

```
@api-service/src/types/user.ts @web-frontend/src/hooks/useAuth.ts

The User type in the API doesn't match the frontend hook.
Show me the differences and suggest how to share the type.
```

### Sharing Types Between Projects

Use project rules to guide cross-project imports:

```yaml
# .cursor/rules/monorepo-imports.mdc (in monorepo root)
---
description: "Monorepo import conventions"
globs: ""
alwaysApply: true
---
# Import Rules
- Shared types: import from @myorg/shared (never relative paths across packages)
- Shared UI: import from @myorg/ui
- Never import directly from another app package (apps/api → apps/web is forbidden)
- Each package declares its own dependencies in package.json
```

## Rules Inheritance

### Monorepo: Root + Package Rules

```
monorepo/
├── .cursor/rules/
│   ├── global.mdc              # alwaysApply: true (applies everywhere)
│   └── security.mdc            # alwaysApply: true
├── packages/
│   ├── api/
│   │   └── .cursor/rules/
│   │       └── api-patterns.mdc  # Scoped to api/ files
│   ├── web/
│   │   └── .cursor/rules/
│   │       └── react-patterns.mdc  # Scoped to web/ files
│   └── shared/
```

**Behavior:**
- Root rules apply to all files in the monorepo
- Package-level rules apply only when editing files in that package
- If both match, both are included in context

### Multi-Root: Independent Rules

In a multi-root workspace, each root has its own `.cursor/rules/`:

```
# Workspace contains:
api-service/
  .cursor/rules/express-patterns.mdc    # Only applies to api-service files

web-frontend/
  .cursor/rules/react-patterns.mdc      # Only applies to web-frontend files
```

Rules do NOT cross workspace roots. Each project's rules are independent.

## Selective Indexing Strategies

### Strategy 1: Single Package Focus

```bash
cursor packages/api/
# Only indexes packages/api/
# Fast, focused, no cross-package noise
```

### Strategy 2: Related Packages

```gitignore
# .cursorignore at monorepo root
packages/*/
!packages/api/
!packages/shared/
!packages/config/
```

### Strategy 3: Full Monorepo with Heavy Exclusions

```gitignore
# .cursorignore
node_modules/
dist/
build/
.turbo/
.next/
coverage/
*.lock
*.min.js
**/*.test.ts       # Optional: exclude tests from indexing
**/fixtures/       # Test fixtures
**/migrations/     # Database migrations (reference via @Files)
```

## Performance Optimization

### Memory Management

Each open workspace root consumes memory for indexing. Minimize open roots:

```
# Instead of opening 5 repos:
cursor repo1/ repo2/ repo3/ repo4/ repo5/   # Heavy

# Open only what you need:
cursor repo1/                                # Light
# Add repo2/ only when needed via File > Add Folder
```

### Large Monorepo Tips

```
1. Use .cursorignore aggressively
2. Open specific packages, not the root
3. Close workspace folders you're not actively editing
4. Start new chats when switching between packages
5. Use @Files for cross-package references instead of @Codebase
```

## Enterprise Considerations

- **Repository access**: Multi-root workspaces respect filesystem permissions. Cursor cannot index repos the user cannot read.
- **Indexing scope**: Only open workspace folders are indexed. Opening a shared drive or network mount may be slow.
- **Rule governance**: In monorepos, root-level rules serve as team-wide governance. Package-level rules add specificity.
- **CI alignment**: `.cursor/rules/` should be reviewed in PRs like any other configuration change.

## Resources

- [VS Code Multi-Root Workspaces](https://code.visualstudio.com/docs/editor/multi-root-workspaces)
- [Codebase Indexing](https://docs.cursor.com/context/codebase-indexing)
- [Cursor Rules](https://docs.cursor.com/context/rules)
