---
name: windsurf-reference-architecture
description: |
  Implement Windsurf reference architecture with optimal project structure and AI configuration.
  Use when designing workspace configuration for Windsurf, setting up team standards,
  or establishing architecture patterns that maximize Cascade effectiveness.
  Trigger with phrases like "windsurf architecture", "windsurf project structure",
  "windsurf best practices", "windsurf team setup", "optimize for cascade".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, architecture, configuration, team-setup]

---
# Windsurf Reference Architecture

## Overview
Complete project architecture optimized for Windsurf AI. Covers workspace configuration, rules hierarchy, workflow organization, and team standardization patterns that maximize Cascade's effectiveness.

## Prerequisites
- Windsurf IDE installed
- Team agreement on coding standards
- Repository with consistent project structure

## Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│              Windsurf Workspace                       │
│  ┌───────────────┐  ┌────────────────────────────┐    │
│  │ .windsurfrules│  │ .windsurf/                 │    │
│  │ (AI context)  │  │  ├── rules/ (trigger rules)│    │
│  │               │  │  ├── workflows/ (automation)│    │
│  │               │  │  └── settings.json         │    │
│  └───────────────┘  └────────────────────────────┘    │
│  ┌───────────────┐  ┌────────────────────────────┐    │
│  │ .codeiumignore│  │ ~/.codeium/                │    │
│  │ (index rules) │  │  ├── global_rules.md       │    │
│  │               │  │  ├── windsurf/memories/    │    │
│  │               │  │  └── windsurf/mcp_config   │    │
│  └───────────────┘  └────────────────────────────┘    │
├──────────────────────────────────────────────────────┤
│              Cascade AI Engine                        │
│  ┌───────────┐  ┌───────────┐  ┌─────────────────┐   │
│  │ Super-    │  │ Cascade   │  │ Command         │   │
│  │ complete  │  │ Write/Chat│  │ (Inline Edit)   │   │
│  │ (Tab)     │  │ (Cmd+L)  │  │ (Cmd+I)         │   │
│  └───────────┘  └───────────┘  └─────────────────┘   │
├──────────────────────────────────────────────────────┤
│              Context Layers                           │
│  Rules > Memories > @Mentions > Open Files > Index   │
└──────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Project File Structure

```
my-project/
├── .windsurfrules              # AI context (stack, patterns, constraints)
├── .codeiumignore              # Indexing exclusions
├── .windsurf/
│   ├── settings.json           # IDE settings (committed)
│   ├── rules/
│   │   ├── testing.md          # trigger: glob **/*.test.ts
│   │   ├── api-routes.md       # trigger: glob src/routes/**
│   │   ├── security.md         # trigger: model_decision
│   │   └── migrations.md       # trigger: manual
│   └── workflows/
│       ├── new-feature.md      # /new-feature
│       ├── deploy-staging.md   # /deploy-staging
│       ├── review-pr.md        # /review-pr
│       └── quality-check.md    # /quality-check
├── src/
│   ├── routes/                 # API route handlers
│   ├── services/               # Business logic
│   ├── repositories/           # Data access
│   └── types/                  # Shared types
├── tests/
│   ├── fixtures/               # Test data factories
│   └── services/               # Service unit tests
└── docs/
    └── architecture.md         # Architecture decisions
```

### Step 2: Rules Hierarchy

```yaml
# Priority order (highest to lowest):
rules_hierarchy:
  1_global_rules:
    path: ~/.windsurf/global_rules.md
    limit: 6000 chars
    scope: All workspaces
    use_for: "Personal coding preferences, universal standards"

  2_windsurfrules:
    path: .windsurfrules (project root)
    limit: 6000 chars
    scope: Current workspace
    use_for: "Project stack, architecture, conventions"

  3_workspace_rules:
    path: .windsurf/rules/*.md
    limit: 12000 chars each
    scope: Triggered by glob, model_decision, or manual
    use_for: "File-type-specific patterns, conditional rules"

  4_memories:
    path: ~/.codeium/windsurf/memories/
    scope: Workspace-specific (auto-generated)
    use_for: "Decisions, discoveries (supplement, don't replace rules)"

# Total active chars: 12000 max (global + workspace rules combined)
# If exceeded: global rules take priority, workspace rules truncated
```

### Step 3: Team Configuration Template

```json
// .windsurf/settings.json (committed to git)
{
  "codeium.indexing.excludePatterns": [
    "node_modules/**", "dist/**", ".next/**",
    "coverage/**", "*.min.js", "**/*.map"
  ],
  "codeium.autocomplete.enable": true,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "biomejs.biome",
  "typescript.tsdk": "node_modules/typescript/lib",
  "files.associations": { "*.css": "tailwindcss" }
}
```

### Step 4: Monorepo Strategy

```
monorepo/
├── .windsurfrules              # Shared conventions (brief)
├── .codeiumignore              # Broad exclusions
├── apps/
│   ├── web/
│   │   └── .windsurfrules      # Next.js-specific rules
│   └── mobile/
│       └── .windsurfrules      # React Native rules
├── packages/
│   ├── api/
│   │   └── .windsurfrules      # Express/Fastify rules
│   └── shared/
│       └── .windsurfrules      # Library conventions
└── .windsurf/
    └── workflows/              # Cross-package workflows

# BEST PRACTICE: Open apps/web/ or packages/api/ directly
# NOT the monorepo root
# Cascade gets focused context per workspace window
```

### Step 5: Context Pinning Strategy

```markdown
## What to Pin in Cascade

Pin files that provide essential context:
- Type definition files (types/*.ts)
- Architecture decision records (docs/adr/)
- API schema files (openapi.yaml)
- Database schema (prisma/schema.prisma, drizzle/schema.ts)

How to pin:
- Click the pin icon next to a file in the Cascade context area
- Pinned files are always included in Cascade's context window
- Limit: pin 3-5 files max (more = diluted context)
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cascade ignores project patterns | Missing/empty .windsurfrules | Add stack and architecture details |
| Rules truncated | Over 12,000 combined chars | Split into workspace rules with triggers |
| Wrong patterns for file type | No glob-triggered rules | Add `.windsurf/rules/` with glob triggers |
| Team inconsistency | No shared config | Commit `.windsurf/` directory to git |
| Slow indexing in monorepo | Root workspace open | Open specific package/app directory |

## Examples

### Minimal .windsurfrules for Any Project
```markdown
# Project: [name]
## Stack: [language] + [framework] + [database]
## Testing: [test framework]
## Conventions:
- [3-5 key coding patterns]
## Don't:
- [2-3 explicit anti-patterns]
```

### Verify Architecture Setup
```bash
set -euo pipefail
echo "=== Windsurf Architecture Check ==="
echo "Rules: $([ -f .windsurfrules ] && wc -c < .windsurfrules || echo 'MISSING') chars"
echo "Ignore: $([ -f .codeiumignore ] && wc -l < .codeiumignore || echo 'MISSING') patterns"
echo "Rules dir: $(ls .windsurf/rules/ 2>/dev/null | wc -l || echo 0) files"
echo "Workflows: $(ls .windsurf/workflows/ 2>/dev/null | wc -l || echo 0) files"
```

## Resources
- [Windsurf Rules Directory](https://windsurf.com/editor/directory)
- [Context Awareness](https://docs.windsurf.com/context-awareness/overview)
- [Cascade Customizations Catalog](https://github.com/Windsurf-Samples/cascade-customizations-catalog)

## Next Steps
For workspace variant strategies, see `windsurf-architecture-variants`.
