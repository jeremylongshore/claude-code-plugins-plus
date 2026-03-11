---
name: windsurf-multi-env-setup
description: |
  Configure Windsurf IDE and Cascade AI across team members and project environments.
  Use when onboarding teams to Windsurf, setting up per-project Cascade configuration,
  or managing Windsurf settings across development, staging, and production contexts.
  Trigger with phrases like "windsurf team setup", "windsurf environments",
  "windsurf multi-project", "windsurf team config", "cascade rules per env".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf Multi-Environment Setup

## Overview
Windsurf is an IDE, not a cloud API -- "multi-environment setup" means configuring Cascade AI context and behavior consistently across team members, projects, and deployment targets. The key configuration files are `.windsurfrules` (AI context per project), `.windsurf/settings.json` (IDE preferences), and `.windsurfignore` (indexing exclusions).

## Prerequisites
- Windsurf IDE installed on developer machines
- Shared git repository for `.windsurfrules` and team config templates
- Team agreement on coding standards per service

## Configuration Strategy

| Scope | Config File | Controls |
|-------|------------|---------|
| Per project | `.windsurfrules` | Cascade AI context, coding patterns |
| Per workspace | `.windsurf/settings.json` | IDE behavior, model selection |
| Indexing | `.windsurfignore` | What Cascade can see |
| CI context | `CODEIUM_API_KEY` env var | Codeium API authentication |

## Instructions

### Step 1: Per-Project Cascade Rules
```markdown
<!-- .windsurfrules - Committed to repo root -->

# Project: PaymentService

## Stack
- Language: TypeScript (strict)
- Framework: Fastify v4
- Database: PostgreSQL with Prisma
- Testing: Vitest

## Architecture Rules
- All handlers in src/routes/ - never business logic
- Business logic in src/services/ only
- Database queries in src/repositories/ only
- Use Result<T, E> pattern for errors, never throw in services

## Naming Conventions
- Route handlers: GET/POST/PUT/DELETE prefix
- Service methods: verb + noun (createUser, findOrder)
- Repository methods: db operations (findById, upsert)

## Testing Requirements
- Unit tests for all service methods
- Integration tests for all route handlers
- No mocking of repositories in integration tests
```

### Step 2: Team-Wide IDE Settings Template
```json
{
  "codeium.indexing.excludePatterns": [
    "node_modules/**",
    "dist/**",
    ".next/**",
    "coverage/**",
    "*.min.js",
    "**/*.map",
    "**/*.lock"
  ],
  "codeium.autocomplete.enable": true,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "biomejs.biome",
  "typescript.tsdk": "node_modules/typescript/lib",
  "codeium.chat.preferredModel": "claude-sonnet"
}
```
Store as `.windsurf/settings.json` and commit. Developers can extend with personal overrides in their local settings.

### Step 3: Monorepo Multi-Service Setup
```bash
# Each service gets its own .windsurfrules
monorepo/
  services/
    auth/
      .windsurfrules    # Auth service context (JWT, OAuth flows)
      .windsurfignore
    payments/
      .windsurfrules    # Payments context (Stripe, PCI rules)
      .windsurfignore
    notifications/
      .windsurfrules    # Notification context (queues, templates)
      .windsurfignore
  .windsurf/
    settings.json       # Shared IDE settings
    team-config.md      # Team usage guidelines
```

### Step 4: Onboarding Script for New Developers
```bash
#!/bin/bash
# scripts/setup-windsurf.sh

echo "Setting up Windsurf for this project..."

# Install recommended extensions
windsurf --install-extension esbenp.prettier-vscode
windsurf --install-extension dbaeumer.vscode-eslint

# Verify .windsurfrules exists
if [ ! -f ".windsurfrules" ]; then
  echo "WARNING: .windsurfrules not found. Cascade will lack project context."
fi

# Set Codeium API key if provided
if [ -n "$CODEIUM_API_KEY" ]; then
  windsurf --set "codeium.apiKey" "$CODEIUM_API_KEY"
fi

echo "Windsurf setup complete. Open your service directory (not the monorepo root) for best Cascade performance."
```

### Step 5: CI Environment for Cascade Batch Tasks
```yaml
# .github/workflows/cascade-tasks.yml
# Run Windsurf Cascade in headless mode for automated tasks
name: Cascade Automation
on: workflow_dispatch
  inputs:
    task:
      description: "Cascade task to run"

jobs:
  cascade:
    runs-on: ubuntu-latest
    env:
      CODEIUM_API_KEY: ${{ secrets.CODEIUM_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - name: Run Cascade task
        run: windsurf --cascade --task "${{ inputs.task }}" --output cascade-output.md
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cascade lacks project context | `.windsurfrules` missing or empty | Add stack + patterns to rules file |
| Slow indexing | Monorepo root open with no ignore rules | Open service subdirectory, add `.windsurfignore` |
| Inconsistent team suggestions | No shared settings | Commit `.windsurf/settings.json` to repo |
| Cascade touches wrong files | Too broad workspace scope | Open specific service directory per task |

## Examples

### Quick Project Health Check
```bash
# Verify Windsurf config is in place
ls -la .windsurfrules .windsurfignore .windsurf/settings.json
```

### Per-Environment .windsurfrules
```markdown
<!-- For staging/production deployment scripts -->
# Deployment Context
- Target: AWS ECS on us-east-1
- Container registry: 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp
- Secrets: AWS Secrets Manager (prefix: myapp/production/)
- Do NOT hardcode credentials or environment-specific values
```

## Resources
- [Windsurf Rules Documentation](https://docs.windsurf.com/windsurf/rules)
- [Codeium Team Configuration](https://codeium.com/blog/team-configuration)
- [Windsurf IDE Documentation](https://docs.windsurf.com)

## Next Steps
For architecture best practices, see `windsurf-reference-architecture`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale