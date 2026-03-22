---
name: supabase-architecture-variants
description: |
  Choose and implement Supabase architecture blueprints for different scales:
  monolith, modular monolith, service layer, and microservices.
  Use when designing new Supabase applications, choosing architecture patterns,
  or planning migration paths between architecture tiers.
  Trigger with phrases like "supabase architecture", "supabase blueprint",
  "supabase monolith vs microservices", "supabase project layout", "supabase scale design".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, architecture, scaling]

---
# Supabase Architecture Variants

## Overview
Three validated architecture blueprints for Supabase applications, with clear criteria for choosing each and migration paths between them. Start simple, scale when evidence demands it.

## Prerequisites
- Understanding of team size and traffic requirements
- Supabase project with `@supabase/supabase-js`
- Clear growth projections

## Instructions

### Decision Matrix

| Factor | Monolith | Modular Monolith | Service Layer |
|--------|----------|------------------|---------------|
| Team size | 1-3 devs | 3-8 devs | 8+ devs |
| DAU | < 10K | 10K-100K | 100K+ |
| Deploy frequency | Weekly | Daily | Multiple/day |
| DB tables | < 20 | 20-50 | 50+ (split by domain) |
| Supabase projects | 1 | 1 | Multiple (per service) |
| When to choose | MVP, startup, prototype | Growth stage, feature teams | Enterprise, strict domain boundaries |

### Variant 1: Monolith (Start Here)

```
my-app/
├── supabase/
│   ├── migrations/
│   ├── functions/
│   └── seed.sql
├── src/
│   ├── lib/supabase.ts          # Single client
│   ├── services/                 # All services in one directory
│   │   ├── auth.ts
│   │   ├── todos.ts
│   │   └── payments.ts
│   ├── components/
│   └── pages/
└── tests/
```

```typescript
// src/lib/supabase.ts — single client for everything
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

export const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// All services import from the same client
// src/services/todos.ts
export const TodoService = {
  list: (userId: string) =>
    supabase.from('todos').select('*').eq('user_id', userId),
  create: (todo: TodoInsert) =>
    supabase.from('todos').insert(todo).select().single(),
}
```

**When to upgrade**: Code changes in one domain frequently break another. Deployment contention between teams. Single test suite takes > 10 minutes.

### Variant 2: Modular Monolith

```
my-app/
├── supabase/
│   ├── migrations/
│   └── functions/
├── modules/
│   ├── auth/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types.ts
│   ├── billing/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types.ts
│   ├── projects/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types.ts
│   └── shared/
│       ├── lib/supabase.ts
│       ├── lib/errors.ts
│       └── lib/cache.ts
└── tests/
    ├── auth/
    ├── billing/
    └── projects/
```

```typescript
// modules/shared/lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

export const supabase = createClient<Database>(url, anonKey)
export const supabaseAdmin = createClient<Database>(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
})

// modules/billing/services/subscription-service.ts
// Each module owns its Supabase queries and types
import { supabase } from '../../shared/lib/supabase'

type Subscription = Database['public']['Tables']['subscriptions']['Row']

export const SubscriptionService = {
  async getByOrg(orgId: string): Promise<Subscription | null> {
    const { data } = await supabase
      .from('subscriptions')
      .select('id, plan, status, current_period_end')
      .eq('organization_id', orgId)
      .single()
    return data
  },

  // Module boundary: billing module does NOT query projects table directly
  // Instead, it exposes events or APIs that the projects module consumes
}

// modules/projects/services/project-service.ts
import { supabase } from '../../shared/lib/supabase'
import { SubscriptionService } from '../../billing/services/subscription-service'

export const ProjectService = {
  async create(orgId: string, project: ProjectInsert) {
    // Cross-module call through service interface, NOT direct table query
    const subscription = await SubscriptionService.getByOrg(orgId)
    if (subscription?.plan === 'free') {
      const { count } = await supabase
        .from('projects')
        .select('*', { count: 'exact', head: true })
        .eq('organization_id', orgId)
      if ((count ?? 0) >= 3) throw new Error('Free plan limited to 3 projects')
    }

    return supabase.from('projects').insert(project).select().single()
  },
}
```

**Module rules**:
- Each module owns its tables and services
- Cross-module access goes through service interfaces, never direct table queries
- Shared module provides infrastructure (client, errors, cache)
- Tests are organized by module

**When to upgrade**: Modules need independent deployment. Teams have conflicting scaling needs. Database becomes a bottleneck at > 500 tables.

### Variant 3: Service Layer (Multi-Project)

```
platform/
├── services/
│   ├── auth-service/           # Own Supabase project
│   │   ├── supabase/
│   │   ├── src/
│   │   └── package.json
│   ├── billing-service/        # Own Supabase project
│   │   ├── supabase/
│   │   ├── src/
│   │   └── package.json
│   └── projects-service/       # Own Supabase project
│       ├── supabase/
│       ├── src/
│       └── package.json
├── gateway/                    # API gateway / BFF
│   └── src/
└── shared/
    ├── types/
    └── contracts/              # Service interface definitions
```

```typescript
// services/billing-service/src/supabase.ts
// Each service has its own Supabase project and types
import { createClient } from '@supabase/supabase-js'
import type { BillingDatabase } from './database.types'

export const supabase = createClient<BillingDatabase>(
  process.env.BILLING_SUPABASE_URL!,
  process.env.BILLING_SUPABASE_KEY!
)

// gateway/src/routes/projects.ts
// Gateway aggregates across services
import { BillingClient } from '../clients/billing'
import { ProjectsClient } from '../clients/projects'

export async function createProject(req: Request) {
  const subscription = await BillingClient.getSubscription(req.orgId)
  if (!subscription.canCreateProject) {
    return Response.json({ error: 'Plan limit reached' }, { status: 403 })
  }

  const project = await ProjectsClient.create(req.body)
  return Response.json(project)
}
```

**When to choose**: Only when you have clear domain boundaries, independent teams per domain, and empirical evidence that a single database is a bottleneck.

### Migration Path: Monolith → Modular Monolith

1. Identify domain boundaries (auth, billing, projects, etc.)
2. Create module directories; move files without changing functionality
3. Enforce module boundaries: no cross-module direct table access
4. Add service interfaces for cross-module communication
5. Split tests by module
6. Verify all tests pass after restructuring

## Output
- Architecture variant selected based on team and scale criteria
- Project structure implemented following the chosen blueprint
- Module boundaries defined with clear dependency rules
- Migration path documented for future scaling needs

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependency between modules | Missing abstraction | Extract shared interface or use events |
| Performance degradation after modularization | Extra indirection layers | Profile and optimize hot paths; consider denormalization |
| Multi-project sync drift | Migrations not coordinated | Use shared migration CI pipeline |

## Resources
- [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html)
- [Modular Monolith](https://www.kamilgrzybek.com/design/modular-monolith-primer/)
- [Supabase Architecture](https://supabase.com/docs/guides/getting-started/architecture)

## Next Steps
For common anti-patterns, see `supabase-known-pitfalls`.
