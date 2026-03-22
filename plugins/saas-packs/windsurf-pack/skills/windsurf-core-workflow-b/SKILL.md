---
name: windsurf-core-workflow-b
description: |
  Execute Windsurf's secondary workflow: Workflows, Memories, and reusable automation.
  Use when creating reusable Cascade workflows, managing persistent memories,
  or automating repetitive development tasks.
  Trigger with phrases like "windsurf workflow", "windsurf automation",
  "windsurf memories", "cascade workflow", "windsurf slash command".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, workflows, memories, automation]

---
# Windsurf Core Workflow B — Workflows & Memories

## Overview
Windsurf Workflows are reusable, multi-step automation sequences saved as markdown files and invoked via slash commands in Cascade. Memories are persistent facts that survive across sessions. Together they eliminate repetitive prompting and maintain project context.

## Prerequisites
- Windsurf with Cascade enabled
- Understanding of `windsurf-core-workflow-a` (Write mode)
- `.windsurfrules` configured

## Instructions

### Step 1: Create a Workflow File

Workflows live in `.windsurf/workflows/` as markdown files. Each becomes a slash command.

```markdown
<!-- .windsurf/workflows/new-feature.md -->
---
name: new-feature
description: Scaffold a new feature with service, route, and tests
---

## Steps

1. Ask the user for: feature name, description, and which database tables are involved
2. Create `src/services/${feature-name}.ts` with:
   - CRUD methods using Result<T,E> pattern
   - Input validation with zod schemas
   - JSDoc comments on all public methods
3. Create `src/routes/${feature-name}.ts` with:
   - GET, POST, PUT, DELETE route handlers
   - Request validation middleware
   - Consistent error response format
4. Create `tests/services/${feature-name}.test.ts` with:
   - Unit tests for all service methods
   - Both success and error paths
5. Run `npx vitest run tests/services/${feature-name}.test.ts`
6. If tests pass, report success. If not, fix and re-run.
```

Invoke in Cascade: `/new-feature`

### Step 2: Build a Deployment Workflow

```markdown
<!-- .windsurf/workflows/deploy.md -->
---
name: deploy
description: Deploy to staging with pre-flight checks
---

## Pre-Flight Checks
1. Run `npm run typecheck` — stop if errors
2. Run `npm test` — stop if failures
3. Run `npm run lint` — stop if errors
4. Check `git status` — stop if uncommitted changes

## Deploy
5. Run `git push origin HEAD`
6. Run `npm run build`
7. Run `npm run deploy:staging`

## Post-Deploy
8. Run `curl -sf https://staging.example.com/health | jq .`
9. Report deploy status with health check result
```

### Step 3: Enable Turbo Annotations in Workflows

Add turbo annotations to auto-execute specific commands:

```markdown
<!-- In any workflow step -->
Run the following command:
```bash
// turbo
npm run typecheck
```

Or auto-run all commands in the workflow:
```markdown
// turbo-all
```

Turbo annotations respect allow/deny lists configured in settings.

### Step 4: Manage Cascade Memories

Memories persist facts across sessions. They are auto-generated or manually created.

**Create a memory manually:**
```
Cascade prompt: "Remember that our API uses snake_case for JSON
field names but camelCase for TypeScript interfaces. We transform
with a middleware layer in src/middleware/transform.ts."
```

**View and manage memories:**
- Click Customizations icon (top-right of Cascade panel)
- Navigate to Memories tab
- Delete outdated memories
- Memories are stored at `~/.codeium/windsurf/memories/`

**Key difference: Rules vs Memories:**

| Aspect | Rules | Memories |
|--------|-------|---------|
| Created by | Developer | Cascade (auto) or developer |
| Stored in | `.windsurfrules` or `.windsurf/rules/` | `~/.codeium/windsurf/memories/` |
| Scope | Workspace or global | Workspace-specific |
| Version controlled | Yes (committed to git) | No (local only) |
| Reliability | High (always applied) | Medium (model decides relevance) |
| Best for | Standards, patterns | Decisions, discoveries |

### Step 5: Chain Workflows Together

Reference other workflows within a workflow:

```markdown
<!-- .windsurf/workflows/release.md -->
---
name: release
description: Full release workflow
---

1. Run /deploy workflow first
2. After staging deploy succeeds, ask user to confirm production deploy
3. Run `npm run deploy:production`
4. Create GitHub release: `gh release create v$(node -p "require('./package.json').version")`
5. Post to #releases channel via webhook
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slash command not found | File not in `.windsurf/workflows/` | Check file location and name |
| Workflow skips steps | Ambiguous instructions | Use numbered steps with clear conditions |
| Memory not recalled | Low relevance score | Convert important memories to Rules |
| Turbo runs dangerous command | Not in deny list | Add to `cascadeCommandsDenyList` |
| Workflow too long | Over context limit | Split into smaller, composable workflows |

## Examples

### PR Review Workflow
```markdown
<!-- .windsurf/workflows/review-pr.md -->
---
name: review-pr
description: Review current PR changes
---
1. Run `git diff main...HEAD --stat` to see changed files
2. For each changed file, analyze the diff for:
   - Missing error handling
   - Missing tests for new code
   - Security issues (hardcoded secrets, SQL injection)
   - Performance concerns (N+1 queries, missing indexes)
3. Summarize findings as a bulleted list
```

### Code Quality Workflow
```markdown
<!-- .windsurf/workflows/quality-check.md -->
---
name: quality-check
description: Run full code quality suite
---
// turbo-all
1. Run `npm run typecheck`
2. Run `npm run lint`
3. Run `npm test -- --coverage`
4. Report: types, lint issues, test results, coverage percentage
```

## Resources
- [Windsurf Workflows](https://docs.windsurf.com/windsurf/cascade/workflows)
- [Cascade Memories](https://docs.windsurf.com/windsurf/cascade/memories)
- [Workflow Samples](https://github.com/Windsurf-Samples/cascade-customizations-catalog)

## Next Steps
For common errors, see `windsurf-common-errors`.
