---
name: cursor-multi-repo
description: |
  Work with multiple repositories in Cursor. Triggers on "cursor multi repo",
  "cursor multiple projects", "cursor monorepo", "cursor workspace".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Multi-Repository Workflows

## Multi-Repo Strategies

### Options Overview
```
1. Single Repo per Window
   - One Cursor window per repository
   - Clean separation
   - Simple .cursorrules per project

2. Multi-Root Workspace
   - Multiple repos in one workspace
   - Shared context
   - Complex .cursorrules management

3. Monorepo
   - All code in one repository
   - Unified .cursorrules
   - Workspace-specific overrides
```

## Single Repo Per Window

### When to Use
```
Best for:
- Completely separate projects
- Different tech stacks
- Different teams
- Security isolation needed

Setup:
cursor /path/to/repo1  # Window 1
cursor /path/to/repo2  # Window 2
```

### Cross-Repo Workflow
```
Working across windows:

1. Open both projects
2. Use Cmd+` to switch windows
3. Copy relevant code/context
4. Reference in prompts:
   "In my other project, I have [pattern].
    Create something similar here."
```

## Multi-Root Workspace

### Creating Workspace
```json
// my-workspace.code-workspace
{
  "folders": [
    { "path": "./frontend", "name": "Frontend" },
    { "path": "./backend", "name": "Backend" },
    { "path": "./shared", "name": "Shared" }
  ],
  "settings": {
    "cursor.index.rootFolders": ["frontend", "backend", "shared"]
  }
}
```

### Opening Workspace
```bash
# Open workspace file
cursor my-workspace.code-workspace

# Or via UI
File > Open Workspace from File
```

### Configuration

#### Root .cursorrules
```yaml
# workspace-root/.cursorrules

workspace: my-multi-repo-project

projects:
  frontend:
    framework: react
    language: typescript

  backend:
    framework: express
    language: typescript

  shared:
    type: library
    language: typescript

cross-project-rules:
  - Use shared types from @shared/types
  - API contracts defined in @shared/api
  - Common utils from @shared/utils
```

#### Per-Project Override
```yaml
# frontend/.cursorrules

extends: ../.cursorrules

project: frontend
framework: nextjs

rules:
  - Use App Router patterns
  - Import from @shared for types
  - Use Tailwind for styling
```

### Cross-Project Context
```
Using @-mentions across projects:

"Create a frontend hook that calls
@backend/api/users/route.ts
and uses types from
@shared/types/user.ts"
```

## Monorepo Patterns

### Common Structures
```
# Turborepo/Nx style
monorepo/
├── .cursorrules              # Root rules
├── apps/
│   ├── web/
│   │   ├── .cursorrules      # Web-specific
│   │   └── src/
│   └── api/
│       ├── .cursorrules      # API-specific
│       └── src/
├── packages/
│   ├── ui/
│   ├── shared/
│   └── config/
└── turbo.json
```

### Monorepo .cursorrules
```yaml
# Root .cursorrules

type: monorepo
tool: turborepo

packages:
  apps/web:
    framework: nextjs
    styling: tailwindcss

  apps/api:
    framework: fastify
    database: postgresql

  packages/ui:
    type: component-library
    framework: react

  packages/shared:
    type: shared-library

conventions:
  - Import shared code through package names
  - Types defined in packages/shared
  - UI components from packages/ui
  - Config from packages/config

build:
  - Use turbo for builds
  - Cache artifacts
  - Parallel where possible
```

### Working in Monorepo
```
Tips:

1. Open specific package when focused:
   cursor apps/web

2. Open root for cross-package work:
   cursor .

3. Use @-mentions with full paths:
   @packages/shared/types/user.ts

4. Index only active packages:
   Aggressive .cursorignore
```

## Indexing Strategy

### Selective Indexing
```gitignore
# .cursorignore for multi-repo

# Index only your active work
*

# Include what you're working on
!apps/web/
!packages/shared/
!packages/ui/

# Still exclude heavy stuff
apps/web/node_modules/
apps/web/.next/
```

### Per-Project Indexing
```json
// workspace settings
{
  "cursor.index.excludePatterns": [
    "**/node_modules/**",
    "**/.next/**",
    "**/dist/**",
    "apps/legacy/**"  // Don't index old app
  ]
}
```

## Cross-Project Operations

### Shared Type Updates
```
"Update the User type in @packages/shared/types/user.ts:
- Add 'preferences' field
- Then update all usages in:
  - @apps/web (components and hooks)
  - @apps/api (routes and services)"
```

### API Contract Changes
```
"The API endpoint /users is changing:
- Review @apps/api/routes/users.ts
- Update @packages/shared/api/users.ts contract
- Update @apps/web/hooks/useUsers.ts to match
- Update @apps/mobile/api/users.ts"
```

### Dependency Updates
```
"Upgrade React to 19 across all packages:
- Update all package.json files
- Fix breaking changes in:
  - @apps/web
  - @packages/ui
- Update tests
- Verify builds"
```

## Best Practices

### Organization
```
1. Clear project boundaries
2. Shared code in packages/
3. Consistent .cursorrules structure
4. Per-project overrides when needed
```

### Context Management
```
1. Don't load everything at once
2. Use focused windows when possible
3. Strategic .cursorignore
4. Clear @-mentions with full paths
```

### Team Coordination
```
1. Shared .cursorrules in repo
2. Document workspace setup
3. Consistent patterns across projects
4. Regular sync on conventions
```

## Troubleshooting

### "Can't Find File"
```
Check:
- File path is correct
- Not in .cursorignore
- Indexing includes that folder
- Use full path in @-mention
```

### "Context Too Large"
```
Solutions:
- Open single project instead
- Add more to .cursorignore
- Be more specific with @-mentions
- Start fresh chat
```

### "Inconsistent Suggestions"
```
Solutions:
- Verify .cursorrules inheritance
- Check for conflicting rules
- Add explicit context
- Reference specific patterns
```
