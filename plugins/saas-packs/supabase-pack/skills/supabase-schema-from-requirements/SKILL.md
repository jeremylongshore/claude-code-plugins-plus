---
name: supabase-schema-from-requirements
description: |
  Execute Supabase Schema from Requirements - the primary integration path.
  Use when Starting a new project with defined data requirements.
  Trigger with phrases like "supabase schema from requirements",
  "generate database schema with supabase".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Schema from Requirements

## Overview
Generate Supabase database schema from natural language requirements.
This is the primary workflow for starting new Supabase projects.


## Prerequisites
- Completed `supabase-install-auth` setup
- Valid API credentials configured
- Understanding of `supabase-sdk-patterns`
- Domain knowledge for the use case

## Instructions

### Step 1: Initialize
Set up the initial state for the workflow.

```typescript
// Step 1: Initialize the workflow
const client = getClient();
const config = await client.getConfig();
```

### Step 2: Execute
Execute the core operation.

```typescript
// Step 2: Execute the main operation
const result = await client.execute(config);
console.log("Result:", result);
```

### Step 3: Finalize
Complete the workflow and handle cleanup.

```typescript
// Step 3: Finalize and cleanup
await client.finalize(result);
console.log("Workflow complete");
```

## Output
- Successful completion of Schema from Requirements
- Result data returned from Supabase API
- Confirmation of workflow execution
- Logs showing each step completion

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Initialization Failed | Missing configuration | Check environment variables and config |
| Execution Error | Invalid input data | Validate input before execution |
| Timeout | Long-running operation | Increase timeout or use async pattern |
| Rate Limit | Too many requests | Implement backoff, see `supabase-rate-limits` |

## Examples

### Complete Workflow Example
```typescript
// Complete workflow example
import { getClient } from "./client";

async function runWorkflow() {
  const client = getClient();
  
  // Step 1: Initialize
  const config = await client.getConfig();
  
  // Step 2: Execute
  const result = await client.execute(config);
  
  // Step 3: Finalize
  await client.finalize(result);
  
  return result;
}

runWorkflow().then(console.log).catch(console.error);
```

### Workflow Variations
- **Variation 1**: Batch processing - process multiple items
- **Variation 2**: Async mode - fire and forget with callback
- **Variation 3**: Dry run - validate without executing

## Resources
- [Supabase Schema from Requirements Guide](https://supabase.com/docs/workflows)
- [API Reference](https://docs.supabase.com/api)
- [Best Practices](https://supabase.com/docs/best-practices)

## Next Steps
For secondary workflow, see `supabase-auth-storage-realtime-core`.