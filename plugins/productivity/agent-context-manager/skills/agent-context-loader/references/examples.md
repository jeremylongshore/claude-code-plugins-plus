# Examples

## Example 1: Monorepo with Per-Package Agent Instructions

A monorepo where the root `AGENTS.md` sets global conventions and individual
packages add supplemental rules.

**Directory structure:**

```
my-monorepo/
├── AGENTS.md                        # Global rules
├── packages/
│   ├── api/
│   │   └── AGENTS.md                # API-specific rules
│   ├── web/
│   │   └── AGENTS.md                # Frontend-specific rules
│   └── shared/
│       └── (no AGENTS.md)           # Inherits global only
└── .git/
```

**Root AGENTS.md:**

```markdown
# Project Agent Instructions

## Conventions
- Use TypeScript strict mode in all packages
- Run `pnpm test` before committing
- Commit messages follow Conventional Commits
- Never modify package-lock.json files (we use pnpm)

## Architecture
- Monorepo managed with pnpm workspaces
- Shared types in packages/shared/
- API and web packages import from shared
```

**packages/api/AGENTS.md:**

```markdown
# API Package Instructions

## Conventions
- Use Fastify for HTTP routes (not Express)
- All routes must have OpenAPI schema annotations
- Database queries go through Drizzle ORM, never raw SQL
- Run `pnpm test:api` for package-specific tests
```

**packages/web/AGENTS.md:**

```markdown
# Web Package Instructions

## Conventions
- Use Next.js App Router (not Pages Router)
- Components use functional style with hooks
- CSS uses Tailwind v4 utility classes only
- Images must use next/image for optimization
```

**Discovery output when working in `packages/api/`:**

```
Agent Context Loader — Discovery Results
═══════════════════════════════════════════

Scan root: /home/user/my-monorepo (detected via .git/)

Files discovered (load order):
  1. /home/user/my-monorepo/AGENTS.md
     Depth: 0 (root)
     Instructions: 4 conventions, 1 architecture block
     Status: Loaded

  2. /home/user/my-monorepo/packages/api/AGENTS.md
     Depth: 2 (packages/api)
     Instructions: 4 conventions
     Status: Loaded

Merged context:
  - TypeScript strict mode (root)
  - Conventional Commits (root)
  - pnpm workspaces (root)
  - Fastify for HTTP (api — supplements root)
  - OpenAPI annotations (api — supplements root)
  - Drizzle ORM (api — supplements root)

Conflicts: None detected
Cache: Fresh (first scan this session)
```

## Example 2: Nested Workspace with Conflicting Directives

Two `AGENTS.md` files contain contradictory instructions. The deeper
(more specific) file takes precedence with a warning.

**Root AGENTS.md:**

```markdown
## Git Workflow
- Always sign commits with GPG
- Squash merge all PRs
```

**services/legacy/AGENTS.md:**

```markdown
## Git Workflow
- Skip commit signing (legacy CI does not support GPG)
- Use merge commits (preserve full history)
```

**Discovery output:**

```
Agent Context Loader — Discovery Results
═══════════════════════════════════════════

Files discovered:
  1. /project/AGENTS.md (depth 0)
  2. /project/services/legacy/AGENTS.md (depth 2)

Conflicts detected:
  ⚠ CONFLICT: Commit signing
    Root:    "Always sign commits with GPG"
    Override: "Skip commit signing" (services/legacy)
    Applied: Skip commit signing (deeper directive wins)

  ⚠ CONFLICT: Merge strategy
    Root:    "Squash merge all PRs"
    Override: "Use merge commits" (services/legacy)
    Applied: Use merge commits (deeper directive wins)

Resolution policy: More specific (deeper) directives override general ones.
Review these conflicts to confirm the overrides are intentional.
```

## Example 3: First-Time Setup — No Agent Files Found

A freshly cloned repository with no `AGENTS.md` anywhere in the tree.

**Discovery output:**

```
Agent Context Loader — Discovery Results
═══════════════════════════════════════════

Scan root: /home/user/new-project (detected via .git/)

Files discovered: 0

No AGENTS.md files found in the project tree.

Suggestion: Create an AGENTS.md at the repository root with a minimal template:

  /home/user/new-project/AGENTS.md

Minimal template:
  # Agent Instructions

  ## Conventions
  - [Your coding conventions here]

  ## Architecture
  - [Project architecture notes here]

  ## Workflow
  - [Git workflow, testing, and deployment rules here]
```

## Example 4: Deep Hierarchy with Multiple Override Levels

A large project with three levels of agent instructions, each adding or
overriding the previous.

**Structure:**

```
enterprise-app/
├── AGENTS.md                         # Company-wide standards
├── services/
│   ├── AGENTS.md                     # Service-layer conventions
│   └── payment/
│       └── AGENTS.md                 # Payment-specific compliance rules
```

**Discovery output when working in `services/payment/`:**

```
Agent Context Loader — Discovery Results
═══════════════════════════════════════════

Files discovered (load order):
  1. /enterprise-app/AGENTS.md (depth 0)
     - Code review required for all PRs
     - Use company ESLint config
     - Deploy via ArgoCD only

  2. /enterprise-app/services/AGENTS.md (depth 1)
     - All services must have health check endpoints
     - Use structured logging (JSON format)
     - Database migrations via Flyway

  3. /enterprise-app/services/payment/AGENTS.md (depth 2)
     - PCI-DSS compliance: never log card numbers
     - Encrypt all PII at rest and in transit
     - Two-person review required for payment logic changes
     - Code review required for all PRs (inherits from root, no conflict)

Merged instruction set (9 total):
  From root (3):     code review, ESLint config, ArgoCD deploy
  From services (3): health checks, structured logging, Flyway migrations
  From payment (3):  PCI-DSS logging, PII encryption, two-person review

Conflicts: None (payment adds compliance rules, does not contradict parent)
```

## Example 5: Session Cache Reuse

On the second activation within the same session, cached results are
returned without re-scanning the filesystem.

**First activation:**

```
Agent Context Loader — Discovery Results
═══════════════════════════════════════════
Scan: Full filesystem traversal
Files discovered: 3
Time: 45ms
Cache: Fresh (stored for session)
```

**Second activation (same session):**

```
Agent Context Loader — Discovery Results
═══════════════════════════════════════════
Scan: Skipped (using session cache)
Files discovered: 3 (cached)
Time: <1ms
Cache: Reused (age: 12 minutes)

Note: Run with --refresh to force a new scan if files have changed.
```

## Example 6: Handling Symlinks and Permission Boundaries

The scanner encounters a symlinked directory and a permission-restricted
parent directory during traversal.

**Structure:**

```
/home/user/project/
├── AGENTS.md
├── packages/ → /opt/shared-packages/  (symlink)
└── .git/

/opt/shared-packages/
├── AGENTS.md       # Would be found if symlink followed
└── core/
```

**Discovery output:**

```
Agent Context Loader — Discovery Results
═══════════════════════════════════════════

Scan root: /home/user/project (detected via .git/)

Files discovered:
  1. /home/user/project/AGENTS.md (depth 0)

Warnings:
  ⚠ Symlink skipped: /home/user/project/packages/
    Target: /opt/shared-packages/
    Reason: Symlinked directories are not traversed to prevent loops

  ⚠ Parent traversal stopped at: /home/user/
    Reason: .git/ boundary detected at /home/user/project/

Loaded: 1 file
Skipped: 1 symlink
```

## Example 7: Working Directory Outside a Git Repository

When the current directory has no `.git/` ancestor, the scanner limits
its upward traversal to prevent scanning the entire filesystem.

```
Agent Context Loader — Discovery Results
═══════════════════════════════════════════

Scan root: /tmp/scratch-work (no .git/ found in ancestors)

Files discovered:
  Scanned: /tmp/scratch-work/ and immediate children only
  Found: 0 AGENTS.md files

Warning: No git repository detected. Scan limited to current directory
and one level of children to avoid unbounded traversal.

Suggestion: Initialize a git repo or specify the project root explicitly.
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
