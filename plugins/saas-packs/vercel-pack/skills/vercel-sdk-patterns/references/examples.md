## Examples

### Factory Pattern (Multi-tenant)

```typescript
const clients = new Map<string, VercelClient>();

export function getClientForTenant(tenantId: string): VercelClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new VercelClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager

```python
from contextlib import asynccontextmanager
from None import VercelClient

@asynccontextmanager
async def get_vercel_client():
    client = VercelClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation

```typescript
import { z } from 'zod';

const vercelResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
