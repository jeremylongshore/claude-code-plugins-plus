---
name: windsurf-architecture-variants
description: |
  Choose and implement Windsurf validated architecture blueprints for different scales.
  Use when designing new Windsurf integrations, choosing between monolith/service/microservice
  architectures, or planning migration paths for Windsurf applications.
  Trigger with phrases like "windsurf architecture", "windsurf blueprint",
  "how to structure windsurf", "windsurf project layout", "windsurf microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf Architecture Variants

## Overview
Workspace and project architectures for Windsurf AI IDE. How you structure your workspace directly impacts Cascade's effectiveness -- large monorepos, multi-project setups, and team configurations each require different approaches.

## Prerequisites
- Windsurf installed
- Understanding of Cascade's workspace indexing
- Git workflow established

## Instructions

### Step 1: Single Project Workspace (Simple)

**Best for:** Individual developers, single-service projects.

```
my-project/
├── .windsurfignore      # Exclude build artifacts
├── src/
├── tests/
├── package.json
└── README.md
```

Cascade indexes the entire workspace. Keep it focused on one project for best AI context.

### Step 2: Focused Monorepo Windows (Moderate)

**Best for:** Teams with monorepo, multiple services.

```
# DON'T: open the entire monorepo root in Windsurf
# Cascade will index thousands of files, slow context

# DO: open individual service directories
code packages/api/        # One Windsurf window for API
code packages/frontend/   # Another window for frontend
```

```gitignore
# .windsurfignore at monorepo root (if you must open root)
packages/*/node_modules/
packages/*/dist/
packages/*/coverage/
**/build/
**/generated/
```

### Step 3: Multi-Window Team Workflow (Scale)

**Best for:** Large teams, microservices, shared codebase.

```
Developer A: Windsurf -> services/auth/      (auth service)
Developer B: Windsurf -> services/payments/  (payments service)  
Developer C: Windsurf -> shared/libs/        (shared libraries)

# Each developer gets focused Cascade context
# Shared libraries in a separate workspace
```

Team conventions:
```markdown
1. One Windsurf window per service/package
2. Use .windsurfignore in every package
3. Cascade tasks scoped to current workspace only
4. Cross-service changes: open both workspaces
5. Tag cascade commits: git commit -m "[cascade] description"
```

## Decision Matrix

| Factor | Single Project | Focused Monorepo | Multi-Window Team |
|--------|---------------|------------------|-------------------|
| Team Size | 1-2 | 3-10 | 10+ |
| Codebase | < 10K files | 10K-100K files | 100K+ files |
| Cascade Speed | Fast | Moderate | Fast (per window) |
| Setup | None | .windsurfignore | Per-service windows |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cascade is slow | Too many files indexed | Open smaller workspace, add .windsurfignore |
| Wrong file context | Monorepo root open | Open specific service directory |
| Conflicting edits | Multiple devs, same files | Use feature branches per Cascade session |

## Examples

### Optimized .windsurfignore
```gitignore
node_modules/
dist/
build/
.next/
coverage/
*.min.js
*.map
__pycache__/
.venv/
*.log
```

## Resources
- [Windsurf Docs](https://docs.windsurf.com)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale