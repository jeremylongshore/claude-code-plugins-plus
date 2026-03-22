---
name: brightdata-resource-management
description: |
  Execute Bright Data secondary workflow: Resource Management.
  Use when provisioning GPU instances for ML workloads,
  or auto-scaling infrastructure based on demand.
  Trigger with phrases like "brightdata manage resources",
  "provision infrastructure with brightdata".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, brightdata]
---

# Bright Data Resource Management

## Overview
Provision, scale, and manage infrastructure resources programmatically.
The capacity workflow — right-size your infrastructure for demand.


## Prerequisites
- Completed `brightdata-install-auth` setup
- Familiarity with `brightdata-monitor-alert`
- Valid API credentials configured

## Instructions

### Step 1: List Available Resources
```typescript
const resources = await client.resources.list({
  type: 'compute',
  status: 'available',
});
console.log(`${resources.total} compute resources available`);
resources.data.forEach(r => console.log(`  ${r.type}: ${r.specs} — $${r.pricePerHour}/hr`));

```

### Step 2: Provision Instance
```typescript
const instance = await client.instances.create({
  type: 'gpu',
  specs: { gpu: 'A100', vram: '80GB', vcpus: 16, ram: '128GB' },
  region: 'us-east-1',
  image: 'pytorch-2.1-cuda12',
});
console.log(`Instance ${instance.id} provisioning... IP: ${instance.ip}`);

```

### Step 3: Monitor and Scale
```typescript
const metrics = await client.instances.metrics(instance.id, {
  period: '1h',
  metrics: ['gpu_utilization', 'memory_used', 'network_in'],
});
if (metrics.gpu_utilization.avg < 0.2) {
  console.log('GPU underutilized — consider downscaling');
  // await client.instances.resize(instance.id, { type: 'gpu-small' });
}

```

## Output
- Completed Resource Management execution

- Results from Bright Data API

- Success confirmation or error details

## Error Handling
| Aspect | Monitor & Alert | Resource Management |
|--------|------------|------------|
| Use Case | setting up error tracking and alerting for production apps | provisioning GPU instances for ML workloads |
| Complexity | Medium | Medium-High |
| Performance | Standard | Provisioning takes 30s-5min depending on resource type |

## Examples

### Complete Workflow
```typescript
async function autoscale(threshold: number) {
  const instances = await client.instances.list({ status: 'running' });
  const avgUtil = instances.data.reduce((s, i) => s + i.gpuUtil, 0) / instances.data.length;
  if (avgUtil > threshold) {
    await client.instances.create({ type: 'gpu', specs: defaultSpecs });
    console.log('Scaled up: added 1 instance');
  }
}

```

### Error Recovery
```typescript
try {
  const instance = await client.instances.create(config);
  return instance;
} catch (err) {
  if (err.code === 'insufficient_capacity') {
    console.error('No capacity in requested region. Trying fallback...');
    return client.instances.create({ ...config, region: fallbackRegion });
  } else if (err.code === 'quota_exceeded') {
    console.error('Instance quota reached. Request increase from dashboard.');
  }
  throw err;
}

```

## Resources
- [Bright Data Documentation](https://docs.brightdata.com)
- [Bright Data API Reference](https://docs.brightdata.com/api)

## Next Steps
For common errors, see `brightdata-common-errors`.