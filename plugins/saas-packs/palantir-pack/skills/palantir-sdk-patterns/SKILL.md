---
name: palantir-sdk-patterns
description: |
  Apply production-ready Palantir Foundry SDK patterns for Python and TypeScript.
  Use when implementing Foundry integrations, refactoring SDK usage,
  or establishing team coding standards for Foundry API calls.
  Trigger with phrases like "palantir SDK patterns", "foundry best practices",
  "palantir code patterns", "idiomatic foundry SDK".
allowed-tools: Read, Write, Edit
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, sdk, patterns, typescript]
compatible-with: claude-code, codex, openclaw
---

# Palantir SDK Patterns

## Overview
Production-ready patterns for Foundry Platform SDK and OSDK usage. Covers client singletons, typed error handling, pagination helpers, retry logic, and multi-tenant client factories.

## Prerequisites
- Completed `palantir-install-auth` setup
- Familiarity with async/await patterns
- `foundry-platform-sdk` or `@osdk/client` installed

## Instructions

### Step 1: Singleton Client (Python)
```python
# src/foundry_client.py
import os
import foundry
from functools import lru_cache

@lru_cache(maxsize=1)
def get_client() -> foundry.FoundryClient:
    """Thread-safe singleton — cached after first call."""
    auth = foundry.ConfidentialClientAuth(
        client_id=os.environ["FOUNDRY_CLIENT_ID"],
        client_secret=os.environ["FOUNDRY_CLIENT_SECRET"],
        hostname=os.environ["FOUNDRY_HOSTNAME"],
        scopes=["api:read-data", "api:write-data"],
    )
    auth.sign_in_as_service_user()
    return foundry.FoundryClient(auth=auth, hostname=os.environ["FOUNDRY_HOSTNAME"])
```

### Step 2: Typed Error Handling
```python
import foundry
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional

T = TypeVar("T")

@dataclass
class Result(Generic[T]):
    data: Optional[T] = None
    error: Optional[str] = None
    status_code: Optional[int] = None

def safe_call(fn, *args, **kwargs) -> Result:
    """Wrap any Foundry SDK call with structured error handling."""
    try:
        return Result(data=fn(*args, **kwargs))
    except foundry.ApiError as e:
        return Result(error=e.message, status_code=e.status_code)
    except Exception as e:
        return Result(error=str(e))

# Usage
result = safe_call(
    get_client().ontologies.OntologyObject.list,
    ontology="my-company", object_type="Employee", page_size=10,
)
if result.error:
    print(f"Error {result.status_code}: {result.error}")
else:
    print(f"Found {len(result.data.data)} objects")
```

### Step 3: Pagination Helper
```python
def paginate_objects(client, ontology: str, object_type: str, page_size: int = 100):
    """Iterate through all objects with automatic pagination."""
    page_token = None
    while True:
        result = client.ontologies.OntologyObject.list(
            ontology=ontology,
            object_type=object_type,
            page_size=page_size,
            page_token=page_token,
        )
        yield from result.data
        page_token = result.next_page_token
        if not page_token:
            break

# Usage
for emp in paginate_objects(get_client(), "my-company", "Employee"):
    print(emp.properties["fullName"])
```

### Step 4: Retry with Exponential Backoff
```python
import time
import random

def retry_with_backoff(fn, max_retries=3, base_delay=1.0):
    """Retry on 429/5xx with jittered exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except foundry.ApiError as e:
            if attempt == max_retries or e.status_code not in (429, 500, 502, 503):
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            print(f"Retry {attempt + 1}/{max_retries} in {delay:.1f}s (HTTP {e.status_code})")
            time.sleep(delay)
```

### Step 5: TypeScript OSDK Patterns
```typescript
import { createClient, type Client } from "@osdk/client";
import { createConfidentialOauthClient } from "@osdk/oauth";

// Singleton with lazy initialization
let _client: Client | null = null;

export function getOsdkClient(): Client {
  if (!_client) {
    const oauth = createConfidentialOauthClient(
      process.env.FOUNDRY_CLIENT_ID!,
      process.env.FOUNDRY_CLIENT_SECRET!,
      `https://${process.env.FOUNDRY_HOSTNAME}/multipass/api/oauth2/token`,
    );
    _client = createClient(
      `https://${process.env.FOUNDRY_HOSTNAME}`,
      process.env.ONTOLOGY_RID!,
      oauth,
    );
  }
  return _client;
}
```

## Output
- Thread-safe singleton client with cached auth
- Structured Result type for error handling
- Automatic pagination for large object sets
- Retry logic with jittered backoff

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton | All API calls | One auth flow, reused connection |
| Result wrapper | Error propagation | No uncaught exceptions |
| Pagination helper | Large datasets | Memory-safe iteration |
| Retry with backoff | Transient failures | Resilient operations |

## Examples

### Multi-Tenant Client Factory
```python
_clients: dict[str, foundry.FoundryClient] = {}

def get_client_for_tenant(tenant_id: str) -> foundry.FoundryClient:
    if tenant_id not in _clients:
        hostname = get_tenant_hostname(tenant_id)
        token = get_tenant_token(tenant_id)
        _clients[tenant_id] = foundry.FoundryClient(
            auth=foundry.UserTokenAuth(hostname=hostname, token=token),
            hostname=hostname,
        )
    return _clients[tenant_id]
```

## Resources
- [Foundry Platform SDK](https://github.com/palantir/foundry-platform-python)
- [SDK Reference](https://www.palantir.com/docs/foundry/api/general/overview/sdks)
- [OSDK Overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview)

## Next Steps
Apply patterns in `palantir-core-workflow-a` for real pipeline usage.
