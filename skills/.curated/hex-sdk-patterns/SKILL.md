---
name: hex-sdk-patterns
description: 'Apply production-ready Hex SDK patterns for TypeScript and Python.

  Use when implementing Hex integrations, refactoring SDK usage,

  or establishing team coding standards for Hex.

  Trigger with phrases like "hex SDK patterns", "hex best practices",

  "hex code patterns", "idiomatic hex".

  '
allowed-tools: Read, Write, Edit
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hex
- data
- analytics
compatibility: Designed for Claude Code
---
# Hex SDK Patterns

## Overview

Production patterns for Hex API: typed client, pipeline orchestration, retry logic, and Python integration.

## Instructions

### Step 1: Run with Retry

```typescript
async function runWithRetry(client: HexClient, projectId: string, params: Record<string, any>, maxRetries = 2) {
  for (let i = 0; i <= maxRetries; i++) {
    try {
      const { runId } = await client.runProject(projectId, params);
      const result = await pollUntilComplete(client, projectId, runId);
      return result;
    } catch (err: any) {
      if (i === maxRetries || !err.message.includes('429')) throw err;
      await new Promise(r => setTimeout(r, 30000)); // Wait 30s on rate limit
    }
  }
}
```

### Step 2: Python Client (hextoolkit)

```python
# pip install hextoolkit
from hextoolkit import HexAPI

hex_api = HexAPI(token=os.environ['HEX_API_TOKEN'])

# List projects
projects = hex_api.list_projects()

# Run project
run = hex_api.run_project('project-id', input_params={'date': '2025-01-01'})

# Poll for completion
status = hex_api.get_run_status('project-id', run['runId'])
```

### Step 3: Airflow Integration

```python
# Using the hex-inc/airflow-provider-hex package
from airflow_provider_hex.operators.hex import HexRunProjectOperator

run_task = HexRunProjectOperator(
    task_id='run_hex_project',
    project_id='your-project-id',
    input_params={'date': '{{ ds }}'},
    hex_conn_id='hex_default',
    wait_for_completion=True,
    timeout=600,
)
```

## Prerequisites

- A typed client boundary, secret-manager reference, environment allowlist, and a sandbox project using fictional or approved non-sensitive data.
- An explicit execution budget, idempotency/correlation convention, and policy that unknown project scope or response shape fails closed.

## Output

Produce an SDK receipt with client revision, environment, opaque project/run IDs, parameter schema revision, execution state, aggregate result checks, and rollback/cancel reference. Do not include API tokens, SQL, cell output, or workspace data.

## Error Handling

Classify authentication, authorization, validation, quota, timeout, and terminal-run failures separately. Do not retry a write-like project run without idempotency, broaden scope to bypass a denial, or log notebook output for diagnosis.

## Examples

`sdk=v3; env=sandbox; project=proj-opaque-11; params=r4; run=succeeded; row_count=within-range; cancel=not-needed` is a safe SDK execution receipt.

## Resources

- [Hex API](https://learn.hex.tech/docs/api/api-overview)
- [Airflow Provider](https://github.com/hex-inc/airflow-provider-hex)

## Next Steps

Apply patterns in `hex-core-workflow-a`.
