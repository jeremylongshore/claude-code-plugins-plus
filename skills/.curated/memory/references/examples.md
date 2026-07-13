# Examples

## Example 1: Auto-Loading Memories at Session Start

When a new session begins, the memory skill reads the stored memory file and applies
remembered preferences silently.

**Memory file** (`.claude/memories/project_memory.json`):

```json
{
  "memories": [
    {
      "id": "m-001",
      "text": "Use pnpm as the package manager, never npm or yarn",
      "timestamp": "2026-03-10T14:22:00Z",
      "source": "user-correction"
    },
    {
      "id": "m-002",
      "text": "Project uses Vitest for testing, not Jest",
      "timestamp": "2026-03-10T15:05:00Z",
      "source": "user-preference"
    },
    {
      "id": "m-003",
      "text": "Deploy target is Cloudflare Workers via wrangler CLI",
      "timestamp": "2026-03-11T09:30:00Z",
      "source": "explicit-remember"
    },
    {
      "id": "m-004",
      "text": "Prefer functional components with composables over class-based patterns",
      "timestamp": "2026-03-12T11:00:00Z",
      "source": "user-preference"
    }
  ]
}
```

**Session behavior**:

```
Session start →
  Read .claude/memories/project_memory.json
  Parse 4 memory entries
  Apply silently:
    - Package manager: pnpm (m-001)
    - Test runner: vitest (m-002)
    - Deploy target: Cloudflare Workers (m-003)
    - Code style: functional + composables (m-004)

User: "Add tests for the auth module"
→ Creates auth.test.ts using vitest syntax (imports from 'vitest', uses describe/it/expect)
→ Runs with: pnpm test -- --grep auth
→ No mention of Jest or npm — preferences applied silently
```

## Example 2: Storing New Memories with /remember

The `/remember` command writes a new timestamped entry to the memory file.

```bash
# Store a library preference
/remember "Use zod for all runtime validation, not joi or yup"

# Store an architectural decision
/remember "API routes follow /api/v1/{resource} convention with kebab-case"

# Store a tool preference
/remember "Use biome for formatting instead of prettier + eslint"
```

**Resulting memory file update**:

```json
{
  "id": "m-005",
  "text": "Use zod for all runtime validation, not joi or yup",
  "timestamp": "2026-03-15T10:15:00Z",
  "source": "explicit-remember"
}
```

**Verification**:

```bash
/memories
# Output:
# 1. [2026-03-10] Use pnpm as the package manager, never npm or yarn
# 2. [2026-03-10] Project uses Vitest for testing, not Jest
# 3. [2026-03-11] Deploy target is Cloudflare Workers via wrangler CLI
# 4. [2026-03-12] Prefer functional components with composables over class-based patterns
# 5. [2026-03-15] Use zod for all runtime validation, not joi or yup
```

## Example 3: Implicit Memory Capture from Corrections

When the user corrects a tool choice or approach, the correction is captured
as a memory without needing an explicit `/remember` command.

```
User: "Install the testing library"
Agent: runs `npm install vitest`
User: "No, I said use pnpm"
Agent:
  → Corrects to: pnpm install vitest
  → Stores memory: "User prefers pnpm over npm" (source: user-correction)
  → Future sessions automatically use pnpm
```

**Another implicit capture**:

```
User: "Create a new component"
Agent: Creates a class-based component
User: "We use functional style with setup() here"
Agent:
  → Rewrites as functional component
  → Stores memory: "Prefer functional components with setup() over class-based"
  → All future component creation uses functional style
```

## Example 4: Resolving Conflicting Memories

When a stored memory contradicts a current explicit instruction, the current
instruction wins and the memory is updated.

```
Stored memory: "Deploy target is Cloudflare Workers"
User: "We switched to Vercel, deploy there instead"

Agent behavior:
  1. Detects conflict: stored memory says Cloudflare, user says Vercel
  2. Prioritizes current explicit instruction (Vercel)
  3. Updates memory file:
     - Removes: "Deploy target is Cloudflare Workers"
     - Adds: "Deploy target is Vercel (changed from Cloudflare Workers)"
  4. Proceeds with Vercel deployment
```

## Example 5: Memory Cleanup When Entries Exceed Threshold

When the memory file exceeds 10 entries, low-value entries are removed.

**Before cleanup** (12 entries):

```json
{
  "memories": [
    {"id": "m-001", "text": "Use pnpm", "source": "user-correction"},
    {"id": "m-002", "text": "Use Vitest", "source": "user-preference"},
    {"id": "m-003", "text": "Deploy to Vercel", "source": "explicit-remember"},
    {"id": "m-004", "text": "Functional components", "source": "user-preference"},
    {"id": "m-005", "text": "Use zod for validation", "source": "explicit-remember"},
    {"id": "m-006", "text": "User said hello", "source": "auto-capture"},
    {"id": "m-007", "text": "User acknowledged the change", "source": "auto-capture"},
    {"id": "m-008", "text": "API uses /api/v1/ prefix", "source": "explicit-remember"},
    {"id": "m-009", "text": "Use biome for formatting", "source": "explicit-remember"},
    {"id": "m-010", "text": "User said thanks", "source": "auto-capture"},
    {"id": "m-011", "text": "Database is PostgreSQL via Drizzle ORM", "source": "user-preference"},
    {"id": "m-012", "text": "Auth uses Lucia v3", "source": "explicit-remember"}
  ]
}
```

**After cleanup** (noise removed, high-value kept):

```json
{
  "memories": [
    {"id": "m-001", "text": "Use pnpm", "source": "user-correction"},
    {"id": "m-002", "text": "Use Vitest", "source": "user-preference"},
    {"id": "m-003", "text": "Deploy to Vercel", "source": "explicit-remember"},
    {"id": "m-004", "text": "Functional components", "source": "user-preference"},
    {"id": "m-005", "text": "Use zod for validation", "source": "explicit-remember"},
    {"id": "m-008", "text": "API uses /api/v1/ prefix", "source": "explicit-remember"},
    {"id": "m-009", "text": "Use biome for formatting", "source": "explicit-remember"},
    {"id": "m-011", "text": "Database is PostgreSQL via Drizzle ORM", "source": "user-preference"},
    {"id": "m-012", "text": "Auth uses Lucia v3", "source": "explicit-remember"}
  ]
}
```

Removed entries m-006, m-007, m-010 (greetings, acknowledgments, thanks) as noise.

## Example 6: Forgetting a Memory with /forget

Remove a specific memory when it is no longer relevant.

```bash
/forget "Cloudflare"
# Searches memory entries for "Cloudflare"
# Removes: "Deploy target is Cloudflare Workers"
# Confirms: "Removed 1 memory matching 'Cloudflare'"
```

```bash
/forget "Jest"
# If no match found:
# "No memories matching 'Jest' found. Current memories:"
# (lists all stored memories)
```

## Example 7: Multi-Project Memory Isolation

Each project maintains its own independent memory file. Memories from one project
do not leak into another.

```
~/project-a/.claude/memories/project_memory.json
  → "Use React + Next.js"
  → "Deploy to Vercel"

~/project-b/.claude/memories/project_memory.json
  → "Use Vue + Nuxt"
  → "Deploy to Cloudflare Workers"

When working in project-a:
  → Loads only project-a memories
  → Creates React/Next.js code
  → Deploys to Vercel

When switching to project-b:
  → Loads only project-b memories
  → Creates Vue/Nuxt code
  → Deploys to Cloudflare Workers
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
