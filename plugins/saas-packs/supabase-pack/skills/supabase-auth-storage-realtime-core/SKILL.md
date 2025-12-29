---
name: supabase-auth-storage-realtime-core
description: |
  Execute Supabase Auth + Storage + Realtime - the secondary integration path.
  Use when implementing the secondary use case.
  Trigger with phrases like "supabase auth storage realtime",
  "implement full stack features with supabase".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Auth + Storage + Realtime

## Overview
Implement the core Supabase trifecta: authentication, file storage,
and real-time subscriptions in a single cohesive setup.


## Prerequisites
- Completed `supabase-install-auth` setup
- Understanding of `supabase-schema-from-requirements`
- Valid API credentials configured
- Understanding of the secondary use case

## Instructions

### Step 1: Setup
Configure the workflow for the secondary path.

```typescript
// Step 1: Setup configuration
const client = getClient();
const options = { mode: "secondary" };
```

### Step 2: Process
Execute the secondary processing logic.

```typescript
// Step 2: Process with secondary logic
const result = await client.processSecondary(options);
console.log("Processed:", result);
```

### Step 3: Complete
Finalize the secondary workflow.

```typescript
// Step 3: Complete the workflow
await client.complete(result);
console.log("Secondary workflow complete");
```

## Output
- Successful completion of Auth + Storage + Realtime
- Result data from secondary processing
- Comparison metrics with primary workflow
- Logs showing step-by-step execution

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Setup Failed | Invalid options | Check options configuration |
| Processing Error | Data format mismatch | Validate data before processing |
| Conflict with Primary | Running both workflows | Use workflow locks or sequential execution |
| Rate Limit | Too many requests | Implement backoff, see `supabase-rate-limits` |

## Examples

### Complete Workflow Example
```typescript
// Complete secondary workflow example
import { getClient } from "./client";

async function runSecondaryWorkflow() {
  const client = getClient();
  
  // Step 1: Setup
  const options = { mode: "secondary" };
  
  // Step 2: Process
  const result = await client.processSecondary(options);
  
  // Step 3: Complete
  await client.complete(result);
  
  return result;
}

runSecondaryWorkflow().then(console.log).catch(console.error);
```

### Comparison with Schema from Requirements

| Aspect | Schema from Requirements | Auth + Storage + Realtime |
|--------|------------|------------|
| Use Case | Starting a new project with defined data requirements | Secondary operations |
| Complexity | Medium | Lower |
| Performance | Standard | Optimized |

## Resources
- [Supabase Auth + Storage + Realtime Guide](https://supabase.com/docs/workflows/secondary)
- [Workflow Comparison](https://supabase.com/docs/workflows/comparison)
- [API Reference](https://docs.supabase.com/api)

## Next Steps
For common errors, see `supabase-common-errors`.