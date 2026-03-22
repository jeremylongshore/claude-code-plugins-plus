---
name: flyio-sdk-patterns
description: |
  Apply production-ready Fly.io Machines API patterns for TypeScript with typed
  clients, machine lifecycle management, and multi-region orchestration.
  Trigger: "fly.io Machines API", "fly.io SDK patterns", "fly.io API client".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io SDK Patterns

## Overview

Production-ready patterns for the Fly.io Machines REST API at `https://api.machines.dev`. Typed client, machine lifecycle management, wait-for-state patterns, and multi-region orchestration.

## Instructions

### Pattern 1: Typed Machines API Client

```typescript
const FLY_API = 'https://api.machines.dev';

interface FlyMachine {
  id: string;
  name: string;
  state: 'created' | 'starting' | 'started' | 'stopping' | 'stopped' | 'destroying' | 'destroyed';
  region: string;
  config: {
    image: string;
    guest: { cpu_kind: string; cpus: number; memory_mb: number };
    services: Array<{ ports: Array<{ port: number; handlers: string[] }>; internal_port: number }>;
    env: Record<string, string>;
  };
}

class FlyClient {
  private headers: Record<string, string>;

  constructor(private appName: string, token: string) {
    this.headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  }

  async listMachines(): Promise<FlyMachine[]> {
    const res = await fetch(`${FLY_API}/v1/apps/${this.appName}/machines`, { headers: this.headers });
    return res.json();
  }

  async createMachine(config: FlyMachine['config'], region: string): Promise<FlyMachine> {
    const res = await fetch(`${FLY_API}/v1/apps/${this.appName}/machines`, {
      method: 'POST', headers: this.headers,
      body: JSON.stringify({ region, config }),
    });
    return res.json();
  }

  async stopMachine(id: string): Promise<void> {
    await fetch(`${FLY_API}/v1/apps/${this.appName}/machines/${id}/stop`, {
      method: 'POST', headers: this.headers,
    });
  }

  async waitForState(id: string, state: string, timeout = 30): Promise<void> {
    await fetch(
      `${FLY_API}/v1/apps/${this.appName}/machines/${id}/wait?state=${state}&timeout=${timeout}`,
      { headers: this.headers },
    );
  }
}
```

### Pattern 2: Multi-Region Deployment

```typescript
async function deployToRegions(client: FlyClient, regions: string[], config: FlyMachine['config']) {
  const machines = await Promise.all(
    regions.map(async region => {
      const machine = await client.createMachine(config, region);
      await client.waitForState(machine.id, 'started');
      console.log(`Machine ${machine.id} started in ${region}`);
      return machine;
    })
  );
  return machines;
}

// Deploy to 3 regions
await deployToRegions(client, ['iad', 'lhr', 'nrt'], {
  image: 'registry.fly.io/my-app:latest',
  guest: { cpu_kind: 'shared', cpus: 1, memory_mb: 256 },
  services: [{ ports: [{ port: 443, handlers: ['tls', 'http'] }], internal_port: 3000 }],
  env: { NODE_ENV: 'production' },
});
```

### Pattern 3: Blue-Green Deploy via API

```typescript
async function blueGreenDeploy(client: FlyClient, newImage: string) {
  const oldMachines = await client.listMachines();

  // Create new machines with updated image
  const newMachines = await Promise.all(
    oldMachines.map(m => client.createMachine(
      { ...m.config, image: newImage },
      m.region,
    ))
  );

  // Wait for all new machines to be healthy
  await Promise.all(newMachines.map(m => client.waitForState(m.id, 'started')));

  // Stop old machines
  await Promise.all(oldMachines.map(m => client.stopMachine(m.id)));
  console.log(`Blue-green: ${newMachines.length} new, ${oldMachines.length} stopped`);
}
```

## Resources

- [Machines API Reference](https://fly.io/docs/machines/api/machines-resource/)
- [Working with Machines API](https://fly.io/docs/machines/api/working-with-machines-api/)

## Next Steps

Apply patterns in `flyio-core-workflow-a` for real-world usage.
