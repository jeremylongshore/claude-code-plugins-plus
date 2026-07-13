## Examples

### Factory Pattern (Multi-tenant)

```typescript
const clients = new Map<string, SupabaseClient>();

export function getClientForTenant(tenantId: string): SupabaseClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new SupabaseClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager

```python
from contextlib import asynccontextmanager
from supabase import SupabaseClient

@asynccontextmanager
async def get_supabase_client():
    client = SupabaseClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation

```typescript
import { z } from 'zod';

const supabaseResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
