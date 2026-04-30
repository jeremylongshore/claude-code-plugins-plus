---
name: flyio-sdk-patterns
description: 'Apply production-ready Fly.io Machines API patterns for TypeScript with
  typed

  clients, machine lifecycle management, and multi-region orchestration.

  Trigger: "fly.io Machines API", "fly.io SDK patterns", "fly.io API client".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- edge-compute
- flyio
compatibility: Designed for Claude Code
---
# Fly.io SDK Patterns

## Overview
Production-ready patterns for the Fly.io Machines REST API at `https://api.machines.dev`. Fly.io exposes both GraphQL (organization queries) and REST (machine lifecycle) APIs. The Machines REST API is the primary integration surface for creating, starting, stopping, and destroying VMs across 30+ global regions. A structured client ensures consistent auth, typed machine states, and reliable wait-for-state polling.

## Singleton Client
```typescript
const FLY_API = 'https://api.machines.dev';
let _client: FlyClient | null = null;
export function getClient(appName: string): FlyClient {
  if (!_client) {
    const token = process.env.FLY_API_TOKEN;
    if (!token) throw new Error('FLY_API_TOKEN must be set');
    _client = new FlyClient(appName, token);
  }
  return _client;
}
class FlyClient {
  private h: Record<string, string>;
  constructor(private app: string, token: string) {
    this.h = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  }
  async listMachines(): Promise<FlyMachine[]> {
    const r = await fetch(`${FLY_API}/v1/apps/${this.app}/machines`, { headers: this.h });
    if (!r.ok) throw new FlyError(r.status, await r.text()); return r.json();
  }
  async createMachine(config: MachineConfig, region: string): Promise<FlyMachine> {
    const r = await fetch(`${FLY_API}/v1/apps/${this.app}/machines`, {
      method: 'POST', headers: this.h, body: JSON.stringify({ region, config }) });
    if (!r.ok) throw new FlyError(r.status, await r.text()); return r.json();
  }
  async waitForState(id: string, state: string, timeout = 30): Promise<void> {
    const r = await fetch(`${FLY_API}/v1/apps/${this.app}/machines/${id}/wait?state=${state}&timeout=${timeout}`,
      { headers: this.h });
    if (!r.ok) throw new FlyError(r.status, `Wait for ${state} timed out`);
  }
}
```

## Error Wrapper
```typescript
export class FlyError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = 'FlyError'; }
}
export async function safeCall<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  try { return await fn(); }
  catch (err: any) {
    if (err instanceof FlyError && err.status === 429) { await new Promise(r => setTimeout(r, 2000)); return fn(); }
    if (err instanceof FlyError && err.status === 401) throw new FlyError(401, 'Invalid FLY_API_TOKEN');
    throw new FlyError(err.status ?? 0, `${operation} failed: ${err.message}`);
  }
}
```

## Request Builder
```typescript
class DeployBuilder {
  private regions: string[] = []; private config: Partial<MachineConfig> = {};
  toRegions(...r: string[]) { this.regions = r; return this; }
  withImage(img: string) { this.config.image = img; return this; }
  withGuest(cpus: number, mem: number) { this.config.guest = { cpu_kind: 'shared', cpus, memory_mb: mem }; return this; }
  async execute(client: FlyClient): Promise<FlyMachine[]> {
    return Promise.all(this.regions.map(async r => {
      const m = await client.createMachine(this.config as MachineConfig, r);
      await client.waitForState(m.id, 'started'); return m;
    }));
  }
}
// Usage: await new DeployBuilder().toRegions('iad','lhr','nrt').withImage('app:latest').withGuest(1,256).execute(client);
```

## Response Types
```typescript
type MachineState = 'created' | 'starting' | 'started' | 'stopping' | 'stopped' | 'destroying' | 'destroyed';
interface FlyMachine {
  id: string; name: string; state: MachineState; region: string;
  config: MachineConfig; created_at: string; updated_at: string;
}
interface MachineConfig {
  image: string; guest: { cpu_kind: string; cpus: number; memory_mb: number };
  services: Array<{ ports: Array<{ port: number; handlers: string[] }>; internal_port: number }>;
  env: Record<string, string>;
}
interface FlyVolume { id: string; name: string; region: string; size_gb: number; attached_machine_id: string | null; }
```

## Testing Utilities
```typescript
export function mockMachine(overrides: Partial<FlyMachine> = {}): FlyMachine {
  return { id: 'mach-001', name: 'test-machine', state: 'started', region: 'iad',
    config: { image: 'app:latest', guest: { cpu_kind: 'shared', cpus: 1, memory_mb: 256 }, services: [], env: {} },
    created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z', ...overrides };
}
```

## Error Handling
| Pattern | When to Use | Example |
|---------|-------------|---------|
| `safeCall` wrapper | All Machines API calls | Catches network + API errors uniformly |
| Retry on 429 | Bulk machine creation | 2s delay before retry |
| `waitForState` timeout | After create/start/stop | Prevents hanging deploys |
| Region fallback | Multi-region deploy failure | Skip failed region, continue others |

## Resources
- [Machines API Reference](https://fly.io/docs/machines/api/machines-resource/)

## Next Steps
Apply patterns in `flyio-core-workflow-a`.
