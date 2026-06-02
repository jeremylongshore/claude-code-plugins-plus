# Project Analysis

On first `/hyperflow` session in a project, analyze the entire codebase and generate a profile in `.hyperflow/`. On subsequent sessions, the **thinking model** evaluates staleness and decides what to refresh — it never blindly regenerates.

## Decision Tree (Thinking Model Executes This)

The thinking model runs this decision tree at session start. No workers are dispatched until this completes.

```
Step 1: Does .hyperflow/ exist at project root?
    │
    NO → Go to FULL ANALYSIS
    │
    YES → Step 2: Does .hyperflow/.checksums exist and parse correctly?
           │
           NO → Go to FULL ANALYSIS
           │
           YES → Step 3: Compute current SHA256 of every tracked config file
                  that exists on disk (see "Config Files to Track" below)
                  │
                  Step 4: Compare each hash against .checksums
                  │
                  ├─ ALL MATCH + no new config files appeared
                  │  → SKIP ANALYSIS entirely
                  │    Print "Analysis cache fresh — skipping"
                  │    The thinking model reads cached .hyperflow/*.md directly
                  │    Zero agents dispatched for analysis
                  │
                  ├─ SOME CHANGED, ADDED, or REMOVED
                  │  → PARTIAL REFRESH
                  │    Use the Staleness Mapping table to find affected analysis files
                  │    Dispatch searcher agents ONLY for those specific analysis files
                  │    Print "Refreshing — profile.md, dependencies.md" (example)
                  │    Rewrite .checksums with all current hashes
                  │
                  └─ ALL CHANGED (e.g., major refactor, new project)
                     → FULL ANALYSIS
                       Dispatch 6 parallel searcher agents
                       Regenerate everything
```

### Enforcement Rules

1. **No agents if fresh.** If all checksums match, zero searcher agents are dispatched. The thinking model reads cached files with the Read tool.
2. **Partial over full.** If only `package.json` changed, only `profile.md`, `dependencies.md`, and `testing.md` get refreshed. The other 3 files are untouched.
3. **Thinking model decides.** Staleness evaluation is never delegated to a worker agent. The thinking model runs `sha256sum`, compares, and decides.
4. **New files trigger refresh.** A config file appearing on disk that wasn't in `.checksums` triggers refresh of its mapped analysis files.
5. **Deleted files trigger refresh.** A config file in `.checksums` that no longer exists triggers refresh of its mapped analysis files.
6. **Folder structure changes.** If the thinking model notices major folder additions/removals (via `ls` or `find`), it refreshes `architecture.md` even if no config checksums changed. This is a judgment call — not every new file warrants it.

## Analysis Files

```
.hyperflow/
├── tasks/              # Active task tracking (auto-cleaned)
├── profile.md          # Project identity + tech stack
├── architecture.md     # Folder structure + component relationships
├── conventions.md      # Naming, patterns, code style
├── dependencies.md     # Key deps + how they're used
├── testing.md          # Test framework, patterns, commands
├── git-workflow.md     # Branch strategy, CI/CD, PR conventions
└── .checksums          # SHA256 of config files for staleness detection
```

### profile.md
Discover: project name (from package.json, Cargo.toml, pyproject.toml), language and runtime version, framework (React, Next.js, Express, Django, etc.), build commands (dev, build, start, lint), entry points, environment setup notes, monorepo structure if applicable.

### architecture.md
Discover: top-level folder map with purpose of each directory, architectural pattern (layered, feature-based, MVC, hexagonal), data flow (frontend: state → UI; backend: request → handler → DB), state management approach, routing structure, API layer pattern (REST, GraphQL, tRPC), key abstractions and base classes.

### conventions.md
Discover from linter configs, editorconfig, and existing code: file naming (kebab-case, PascalCase), variable/function naming (camelCase, snake_case), component patterns (functional only? HOCs?), import ordering, error handling patterns, logging patterns, code style rules from ESLint/Prettier/Biome config.

### dependencies.md
Discover architecturally significant choices only — not a full dependency list:
- UI library (Shadcn, MUI, Chakra) + how it's used
- State management (Redux, Zustand, Context)
- Data fetching (React Query, SWR, fetch, axios)
- Database + ORM (Prisma, Drizzle, TypeORM)
- Auth solution
- Validation library (Zod, Yup, Joi)
- Key utilities (lodash, date-fns)

### testing.md
Discover: test runner (Jest, Vitest, pytest), assertion library, component testing (RTL, Testing Library), E2E framework (Playwright, Cypress, Detox), mocking approach (MSW, jest.mock), test file patterns (co-located, `__tests__/`, `*.test.*`, `*.spec.*`), coverage setup and thresholds, test commands.

### git-workflow.md
Discover: default/main branch name, branch naming conventions (from recent branches), commit message conventions (from recent commits — conventional commits?), CI/CD pipeline (GitHub Actions, GitLab CI) and stages, deploy targets/environments, PR template from `.github/PULL_REQUEST_TEMPLATE.md`, release process.

## Config Files to Track

Check whichever exist on disk. Only include files that are present — don't fail on missing ones.

- `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lock`
- `tsconfig.json`, `jsconfig.json`
- `eslint.config.*`, `.eslintrc*`, `biome.json`, `.prettierrc*`
- `vite.config.*`, `next.config.*`, `webpack.config.*`
- `Dockerfile`, `docker-compose.yml`
- `.github/workflows/*`, `.gitlab-ci.yml`
- `pyproject.toml`, `Cargo.toml`, `go.mod`, `composer.json`

## Staleness Mapping

When a tracked config file's checksum changes (or the file appears/disappears), refresh ONLY the mapped analysis files:

| Changed config file | Refresh these analysis files |
|---|---|
| `package.json`, any lock file | `profile.md`, `dependencies.md`, `testing.md` |
| `tsconfig.json`, `jsconfig.json` | `conventions.md`, `profile.md` |
| `eslint.config.*`, `.eslintrc*`, `.prettierrc*`, `biome.json` | `conventions.md` |
| `vite.config.*`, `next.config.*`, `webpack.config.*` | `profile.md`, `architecture.md` |
| `Dockerfile`, `docker-compose.yml` | `git-workflow.md` |
| `.github/workflows/*`, `.gitlab-ci.yml` | `git-workflow.md` |
| `pyproject.toml`, `Cargo.toml`, `go.mod`, `composer.json` | `profile.md`, `dependencies.md` |

**Deduplication:** If multiple changed files map to the same analysis file, dispatch only ONE searcher for that analysis file — not one per changed config.

### .checksums Format

```
# Hyperflow analysis checksums
# Generated: <ISO-8601 timestamp>
<sha256-hash>  <relative-file-path>
```

Use raw `sha256sum` output format (hash + two-space + path). One line per tracked file. Only files that exist on disk are included.

## Worker Prompt Injection

When dispatching workers, inject only relevant analysis under `## Project Context`. Keep injected content under 50 lines per worker — condense to relevant parts, not the full file.

| Worker role | Inject |
|---|---|
| Implementer | conventions.md + architecture.md + relevant from dependencies.md |
| Writer (tests) | testing.md + conventions.md |
| Writer (docs) | profile.md + architecture.md |
| Searcher | architecture.md |
| Reviewer | All files (full context for quality review) |

## Clarifying Questions

During first analysis, if ambiguity is detected, ask via AskUserQuestion after initial file scanning — not before.

**Trigger conditions:**
- Multiple conflicting configs (e.g., both Jest and Vitest present)
- No clear entry point
- Unclear primary language (e.g., both Python and JS in project)
- No CI/CD config found
- Multiple apps in a monorepo — which is primary?

**Rules:** Max 2-3 questions total. Skip if everything is unambiguous from config files. Use multiple-choice options where possible.

## .gitignore Integration

On first analysis, check if `.hyperflow/` is in `.gitignore`. If not, append:

```
# Hyperflow project analysis (machine-specific)
.hyperflow/
```

If no `.gitignore` exists, create one with just this entry.
