---
name: flyio-deploy-integration
description: |
  Advanced Fly.io deployment strategies including blue-green deployments,
  canary releases, multi-region rollouts, and Machines API orchestration.
  Trigger: "fly.io blue-green", "fly.io canary deploy", "fly.io rolling update".
allowed-tools: Read, Write, Edit, Bash(fly:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Deploy Integration

## Overview

Advanced deployment strategies for Fly.io beyond `fly deploy`. Covers blue-green with the Machines API, canary with traffic splitting, and multi-region coordinated rollouts.

## Instructions

### Strategy 1: Blue-Green via Machines API

```typescript
async function blueGreenDeploy(appName: string, newImage: string) {
  const client = new FlyClient(appName, process.env.FLY_API_TOKEN!);
  const oldMachines = await client.listMachines();

  // 1. Create new machines (green) with updated image
  const greenMachines = await Promise.all(
    oldMachines.map(m => client.createMachine(
      { ...m.config, image: newImage }, m.region
    ))
  );

  // 2. Wait for all green machines to be healthy
  await Promise.all(greenMachines.map(m => client.waitForState(m.id, 'started')));

  // 3. Verify health
  for (const m of greenMachines) {
    const healthy = await checkHealth(`https://${appName}.fly.dev/health`);
    if (!healthy) {
      // Rollback: destroy green, keep blue
      await Promise.all(greenMachines.map(m => client.destroyMachine(m.id)));
      throw new Error('Health check failed — rolled back');
    }
  }

  // 4. Stop old machines (blue)
  await Promise.all(oldMachines.map(m => client.stopMachine(m.id)));
  console.log(`Deploy complete: ${greenMachines.length} new machines`);
}
```

### Strategy 2: Canary with Gradual Rollout

```bash
# Deploy new version to a single machine
fly deploy -a my-app --strategy canary

# Monitor for 10 minutes
fly logs -a my-app --no-tail &
sleep 600

# If healthy, complete rollout
fly deploy -a my-app --strategy rolling

# If unhealthy, rollback
fly releases rollback -a my-app
```

### Strategy 3: Multi-Region Coordinated

```bash
# Deploy region by region
for region in iad lhr nrt; do
  echo "Deploying to $region..."
  fly deploy -a my-app --region $region

  # Health check per region
  curl -sf "https://my-app.fly.dev/health" \
    -H "Fly-Force-Instance-Id: $(fly machine list -a my-app --json | jq -r ".[] | select(.region==\"$region\") | .id" | head -1)"

  echo "Region $region healthy. Continuing..."
done
```

## Resources

- [Fly Deploy](https://fly.io/docs/launch/deploy/)
- [Machines API](https://fly.io/docs/machines/api/)

## Next Steps

For webhook and event handling, see `flyio-webhooks-events`.
