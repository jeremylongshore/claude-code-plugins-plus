# Multi-Root Workspace

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
