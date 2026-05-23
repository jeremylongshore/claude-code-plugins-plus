---
title: "Fixing Provider Registry Mutations and Sandbox Permissions in git-with-intent"
description: "How a mutable global registry caused shared state corruption across tenants, and how Zod validation caught LLM response bugs that TypeScript types couldn't."
date: "2026-02-15"
tags: ["debugging", "typescript", "zod", "registry-pattern", "sandbox", "git-with-intent"]
featured: false
---
## The Bug: Global State Corruption

git-with-intent runs AI agents that interact with LLM providers. Each tenant registers their own custom providers — API keys, model configurations, cost metadata. The `CustomProviderRegistry` managed these registrations.

The problem: registering a custom provider for one tenant polluted the global registry for every other tenant.

```typescript
// BEFORE: Modifies shared global state
register(config: CustomProviderConfig): void {
  const key = `${parsed.provider}:${parsed.model}`;
  this.customProviders.set(key, { config: parsed, registeredAt: Date.now() });

  // These two lines cause the bug:
  (PROVIDER_CAPABILITIES as Record<string, ProviderCapabilities>)[key] = capabilities;
  (PROVIDER_COSTS as Record<string, ProviderCostMetadata>)[key] = costMeta;
}
```

`PROVIDER_CAPABILITIES` and `PROVIDER_COSTS` are module-level constants — shared across the entire Node.js process. When tenant A registers a provider, tenant B sees it. When tenant A unregisters, tenant B loses it. When tests register providers, other tests inherit them.

Three failure modes, all from two lines of code:

1. **Multi-tenant pollution**: One tenant's custom provider appears in another tenant's provider list
2. **Test isolation failure**: Tests that register providers leak state into subsequent tests, creating random failures depending on execution order
3. **Race conditions**: Concurrent register/unregister operations corrupt the global maps

## The Fix: Instance-Only Storage

The solution is to stop touching the globals entirely. Store capabilities and costs inside the registry instance alongside the config:

```typescript
interface RegistryEntry {
  config: CustomProviderConfig;
  capabilities: ProviderCapabilities;  // NEW: Instance storage
  cost: ProviderCostMetadata;          // NEW: Instance storage
  factory?: LLMProviderFactory;
  registeredAt: number;
}

class CustomProviderRegistry {
  private customProviders = new Map<string, RegistryEntry>();

  register(config: CustomProviderConfig): void {
    this.customProviders.set(key, {
      config: parsed,
      capabilities,  // Stored in instance only
      cost,           // Stored in instance only
      registeredAt: Date.now(),
    });
    // No more global mutation
  }
}
```

Lookup methods check the instance first, then fall back to built-in maps:

```typescript
getCapabilities(providerModel: string): ProviderCapabilities | undefined {
  return this.customProviders.get(providerModel)?.capabilities
    ?? PROVIDER_CAPABILITIES[providerModel];
}
```

Custom providers shadow built-in ones through the lookup chain. Each registry instance is fully isolated. No shared state, no cross-tenant pollution, no test leakage.

## Sandbox Permission Enforcement

The same release hardened the sandbox system. The `SandboxedAgent` previously trusted agent configurations without enforcing permission boundaries. Three fixes:

**Deny-by-default network access:**

```typescript
const allowNet = this.permissionProfile.permissions.allowNet;
const networkEnabled = allowNet === true || Array.isArray(allowNet);

this.sandbox = await this.provider.create({
  network: {
    enabled: networkEnabled,  // Only enable if explicitly allowed
    allowedHosts: Array.isArray(allowNet) ? allowNet : undefined,
  },
});
```

If the permission profile doesn't explicitly grant network access, the sandbox has no network. No implicit permissions.

**Destructive operation checks:**

```typescript
commit(): RunArtifact | null {
  if (!this.permissionProfile.allowsDestructive) {
    throw new Error(
      `Agent '${this.options.agentType}' is not permitted to commit`
    );
  }
  return this.worktreeManager.commit(...);
}
```

Same pattern for merge operations. Agents that shouldn't be committing code can't, even if they try. The permission check happens at the operation boundary, not in the agent logic.

**Merge rollback on failure:** If a git merge fails mid-operation, the sandbox now runs `git merge --abort` and restores the original branch. Previously, a failed merge left the worktree in a dirty state that required manual cleanup.

## Zod Catches What TypeScript Misses

The `CoderAgent` parses LLM responses into structured code generation results. The old code used `JSON.parse()` with ad-hoc type casting:

```typescript
// BEFORE: No runtime validation
const parsed = JSON.parse(jsonMatch[0]);
const files = (parsed.files || []).map((f: any) => ({
  path: this.sanitizePath(f.path || ''),
  content: f.content || '',
  action: this.validateAction(f.action), // Manual enum check
  explanation: f.explanation || 'No explanation provided',
}));
```

TypeScript types don't exist at runtime. If the LLM returns `confidence: "95"` (a string instead of a number), TypeScript says nothing. If `action` is `"update"` instead of `"modify"`, the manual enum check silently defaults to `"create"`.

The fix uses Zod schemas for full runtime validation:

```typescript
const CodeGenFileSchema = z.object({
  path: z.string().default(''),
  content: z.string().default(''),
  action: z.enum(['create', 'modify', 'delete']).catch('create'),
  explanation: z.string().default('No explanation provided'),
});

const CodeGenResponseSchema = z.object({
  files: z.array(CodeGenFileSchema).default([]),
  summary: z.string().optional(),
  confidence: z.number().min(0).max(100).catch(50),
  testsIncluded: z.boolean().optional(),
  estimatedComplexity: z.unknown().optional(),
});
```

What Zod catches that TypeScript doesn't:

- **Type coercion**: LLM returns `confidence: "95"` (string) — Zod rejects it, applies `.catch(50)` default
- **Out-of-range values**: `confidence: 150` — Zod enforces `.min(0).max(100)`
- **Invalid enums**: `action: "update"` — Zod's `.enum()` rejects it, `.catch('create')` applies
- **Missing fields**: `files: undefined` — Zod defaults to `[]` instead of passing `undefined` downstream
- **Structural violations**: Completely malformed JSON gets caught at parse time, not three functions later when something tries to iterate over `undefined`

The `validateAction()` helper method was deleted entirely — Zod handles it.

## The Pattern Lesson

Mutable global registries are a recurring source of bugs in multi-tenant systems. The pattern is always the same:

1. Someone creates a module-level map for "shared" data
2. A feature adds write access to that map
3. Everything works in single-tenant tests
4. Multi-tenant or parallel execution reveals the shared state corruption

The fix is also always the same: make the data instance-owned, not module-owned. If you need to look up shared defaults, use a fallback chain — check the instance first, fall back to the module-level constant second. The constant stays read-only. The instance handles all mutations.

For LLM response parsing, the lesson is simpler: TypeScript types are compile-time documentation. They tell you what the response *should* look like. Zod schemas tell you what it *actually* looks like. When your data comes from an LLM that can return literally anything, runtime validation isn't optional.
