---
name: windsurf-reference-architecture
description: |
  Implement Windsurf reference architecture with best-practice project layout.
  Use when designing new Windsurf integrations, reviewing project structure,
  or establishing architecture standards for Windsurf applications.
  Trigger with phrases like "windsurf architecture", "windsurf best practices",
  "windsurf project structure", "how to organize windsurf", "windsurf layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf Reference Architecture

## Overview
Project architecture optimized for Windsurf (Codeium) AI-assisted development. Covers workspace configuration, Cascade AI flow optimization, rules files for context, and team standardization patterns.

## Prerequisites
- Windsurf IDE installed
- Team agreement on coding standards
- Repository with consistent project structure
- Understanding of Cascade AI flows

## Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│              Windsurf Workspace                       │
│  ┌───────────────┐  ┌────────────────────────────┐    │
│  │ .windsurfrules│  │ .windsurf/settings.json    │    │
│  │ (AI context)  │  │ (IDE configuration)        │    │
│  └───────────────┘  └────────────────────────────┘    │
├──────────────────────────────────────────────────────┤
│              Cascade AI Engine                        │
│  ┌───────────┐  ┌───────────┐  ┌─────────────────┐   │
│  │ Inline    │  │ Chat      │  │ Multi-file      │   │
│  │ Complete  │  │ (Cascade) │  │ Edit            │   │
│  └───────────┘  └───────────┘  └─────────────────┘   │
├──────────────────────────────────────────────────────┤
│              Project Structure                        │
│  src/ │ tests/ │ docs/ │ .windsurf/ │ .windsurfrules │
├──────────────────────────────────────────────────────┤
│              Indexing Engine                           │
│  Semantic Index │ File Cache │ Dependency Graph       │
└──────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Create Windsurf Rules File
```markdown
<!-- .windsurfrules - Project context for Cascade AI -->

# Project: MyApp

## Tech Stack
- Framework: Next.js 14 (App Router)
- Language: TypeScript (strict mode)
- Styling: Tailwind CSS v3
- State: Zustand
- Testing: Vitest + React Testing Library
- Database: PostgreSQL with Drizzle ORM

## Architecture Patterns
- Server Components by default, Client Components only when needed
- API routes in app/api/ using Route Handlers
- Shared types in types/ directory
- Business logic in services/ directory
- Database queries in db/ directory

## Coding Standards
- Named exports only, never default exports
- Use async/await, never raw Promises
- All functions must have JSDoc comments
- Error handling: use Result pattern, never throw in services
- Use zod for all runtime validation
```

### Step 2: Configure Workspace Settings
```json
{
  "codeium.indexing.excludePatterns": [
    "node_modules/**",
    ".next/**",
    "dist/**",
    "coverage/**",
    "*.min.js",
    "**/*.map"
  ],
  "codeium.autocomplete.enable": true,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "biomejs.biome",
  "typescript.tsdk": "node_modules/typescript/lib",
  "files.associations": {
    "*.css": "tailwindcss"
  }
}
```

### Step 3: Team Configuration Template
```json
// .windsurf/team-config.json - Shared team settings
{
  "cascade": {
    "preferredModels": ["claude-sonnet", "gpt-4o"],
    "contextRules": {
      "maxContextFiles": 15,
      "preferOpenTabs": true,
      "includeTestFiles": true,
      "includeTypeDefinitions": true
    },
    "codeGeneration": {
      "language": "typescript",
      "strictMode": true,
      "includeTypes": true,
      "includeTests": false
    }
  },
  "formatting": {
    "tabSize": 2,
    "useTabs": false,
    "trailingComma": "all",
    "singleQuote": true,
    "printWidth": 100
  }
}
```

### Step 4: Project-Specific Context Files
```typescript
// .windsurf/patterns.md - Common patterns for Cascade
/**
 * API Route Pattern:
 * ```typescript
 * export async function GET(req: NextRequest) {
 *   const params = searchParamsSchema.parse(Object.fromEntries(req.nextUrl.searchParams));
 *   const result = await service.find(params);
 *   return NextResponse.json(result);
 * }
 * ```
 *
 * Service Pattern:
 * ```typescript
 * export async function findById(id: string): Promise<Result<Entity, AppError>> {
 *   const entity = await db.query.entities.findFirst({ where: eq(entities.id, id) });
 *   if (!entity) return err(new NotFoundError('Entity', id));
 *   return ok(entity);
 * }
 * ```
 */
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cascade ignores rules | File not at project root | Place `.windsurfrules` in workspace root |
| Slow indexing | Large repo with no excludes | Add node_modules and dist to excludes |
| Inconsistent suggestions | No team config | Create shared `.windsurf/` directory |
| Wrong framework patterns | Missing context | Add framework details to rules file |

## Examples

### Monorepo Rules File
```markdown
<!-- .windsurfrules for monorepo -->
# Monorepo Structure
- packages/api - Express REST API (Node.js)
- packages/web - Next.js frontend
- packages/shared - Shared TypeScript types and utilities
- packages/db - Database schema and migrations (Drizzle)

When editing files in packages/api, use Express patterns.
When editing files in packages/web, use Next.js App Router patterns.
Always import from @repo/shared for shared types.
```

## Resources
- [Windsurf Documentation](https://docs.windsurf.com)
- [Cascade AI Guide](https://docs.windsurf.com/cascade)
- [Windsurf Rules Reference](https://docs.windsurf.com/rules)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale