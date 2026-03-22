---
name: windsurf-architecture-variants
description: |
  Choose workspace architectures for different project scales in Windsurf.
  Use when deciding how to structure Windsurf workspaces for monorepos,
  multi-service setups, or polyglot codebases.
  Trigger with phrases like "windsurf workspace strategy", "windsurf monorepo",
  "windsurf project layout", "windsurf multi-service", "windsurf workspace size".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, architecture, workspace, monorepo]

---
# Windsurf Architecture Variants

## Overview
How you structure your Windsurf workspace directly impacts Cascade's effectiveness. Large monorepos, multi-service setups, polyglot codebases, and different team sizes each require different approaches. This skill covers workspace strategies from solo projects to 100+ developer organizations.

## Prerequisites
- Windsurf installed
- Understanding of Cascade's workspace indexing model
- Git workflow established

## Instructions

### Variant 1: Single Project (Solo / Small Team)

**Best for:** 1-3 developers, single service, <10K files.

```
my-project/
├── .windsurfrules          # Full project context
├── .codeiumignore          # Exclude build artifacts
├── src/
├── tests/
├── package.json
└── README.md
```

**Configuration:**
- Open entire project as workspace
- Cascade indexes everything — no partitioning needed
- `.windsurfrules` contains complete stack and architecture details

### Variant 2: Focused Monorepo Windows (Medium Team)

**Best for:** 3-15 developers, monorepo with 2-10 packages.

```
monorepo/
├── .windsurfrules          # Brief shared conventions
├── .codeiumignore          # Aggressive exclusions at root
├── packages/
│   ├── api/
│   │   ├── .windsurfrules  # API-specific rules
│   │   └── .codeiumignore
│   ├── web/
│   │   ├── .windsurfrules  # Frontend-specific rules
│   │   └── .codeiumignore
│   └── shared/
│       ├── .windsurfrules  # Library conventions
│       └── .codeiumignore
└── .windsurf/
    └── workflows/          # Shared workflows
```

**Strategy:**
```bash
# Each developer opens their package directory:
windsurf packages/api/        # Backend dev
windsurf packages/web/        # Frontend dev
windsurf packages/shared/     # Library maintainer

# NOT: windsurf monorepo/     # Too broad!
```

### Variant 3: Multi-Window Team Workflow (Large Team)

**Best for:** 15+ developers, microservices, 50K+ total files.

```
Developer A: Windsurf → services/auth/        (auth service)
Developer B: Windsurf → services/payments/    (payments)
Developer C: Windsurf → services/notifications/ (notifications)
Developer D: Windsurf → shared/libs/          (shared libraries)

Each developer gets focused Cascade context per workspace window.
```

**Team conventions:**
```markdown
1. One Windsurf window per service/package
2. Every service has its own .windsurfrules and .codeiumignore
3. Cascade tasks scoped to current workspace only
4. Cross-service changes: open both workspaces side by side
5. Tag cascade commits: git commit -m "[cascade] description"
6. Use shared workflows from central config repo
```

### Variant 4: Polyglot / Multi-Language

**Best for:** Projects with multiple languages (TypeScript + Python + Go).

```
# Each language has different .windsurfrules
services/
├── ts-api/
│   └── .windsurfrules     # TypeScript patterns, Fastify, Vitest
├── python-ml/
│   └── .windsurfrules     # Python patterns, FastAPI, pytest
└── go-gateway/
    └── .windsurfrules     # Go patterns, chi router, go test
```

```markdown
<!-- .windsurfrules for Python service -->
# Project: ML Pipeline

## Stack
- Language: Python 3.11
- Framework: FastAPI
- ML: scikit-learn, pandas
- Testing: pytest with fixtures
- Type checking: mypy (strict)

## Conventions
- Use pydantic for all data models
- Async endpoints with asyncio
- Type hints on all functions
- No print() — use logging module
```

### Variant 5: Frontend-Heavy (Design System)

**Best for:** UI-heavy projects with design system, Storybook, component library.

```markdown
<!-- .windsurfrules for design system -->
# Project: Design System

## Stack
- Framework: React 18 + Next.js 14
- Styling: Tailwind CSS + custom tokens
- Components: Radix UI primitives
- Docs: Storybook 8
- Testing: Vitest + Testing Library

## Component Conventions
- One component per file (ComponentName.tsx)
- Co-located tests: ComponentName.test.tsx
- Co-located stories: ComponentName.stories.tsx
- Props interface exported: ComponentNameProps
- Use forwardRef for all components
- Use CVA (class-variance-authority) for variants

## Design Tokens
- Colors: use design-system/tokens, never raw Tailwind colors
- Spacing: use space-* scale (4px base)
- Typography: use text-* presets
```

**Cascade integration:** Use Previews to iterate on UI components:
```
"Preview the Button component with all variants"
Click elements in Preview → send to Cascade for refinement
```

## Decision Matrix

| Factor | Solo | Focused Mono | Multi-Window | Polyglot |
|--------|------|-------------|-------------|----------|
| Team Size | 1-3 | 3-15 | 15+ | Any |
| Codebase | <10K files | 10K-50K | 50K+ | Mixed |
| Cascade Speed | Fast | Fast (per window) | Fast (per window) | Fast (per window) |
| Setup Effort | Minimal | .codeiumignore + rules | Per-service config | Per-language rules |
| Context Quality | Excellent | Good | Good | Good (per lang) |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cascade is slow | Too many files indexed | Open smaller workspace, add .codeiumignore |
| Wrong file context | Monorepo root open | Open specific service directory |
| Conflicting edits | Multiple devs, same files | Feature branches per Cascade session |
| Wrong language patterns | Multi-language workspace | Separate .windsurfrules per language directory |
| Stale suggestions | Index out of date | Command Palette > "Codeium: Reset Indexing" |

## Examples

### Optimized .codeiumignore (Universal)
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
target/
vendor/
*.log
*.sqlite
```

### Workspace Health Check
```bash
set -euo pipefail
FILE_COUNT=$(find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*' | wc -l)
echo "Indexed files: ~$FILE_COUNT"
[ "$FILE_COUNT" -gt 10000 ] && echo "WARNING: Consider opening a subdirectory"
[ -f .windsurfrules ] && echo "Rules: $(wc -c < .windsurfrules) chars" || echo "Rules: MISSING"
[ -f .codeiumignore ] && echo "Ignore: $(wc -l < .codeiumignore) patterns" || echo "Ignore: MISSING"
```

## Resources
- [Windsurf Context Awareness](https://docs.windsurf.com/context-awareness/overview)
- [Windsurf Ignore](https://docs.windsurf.com/context-awareness/windsurf-ignore)

## Next Steps
For known pitfalls and anti-patterns, see `windsurf-known-pitfalls`.
