# API Migration Examples

## Endpoint Mapping

```json
{
  "mappings": [
    { "legacy": "GET /api/users", "target": "GET /v2/users", "change": "Response wrapped in {data, pagination}" },
    { "legacy": "GET /api/users/:id", "target": "GET /v2/users/:id", "change": "'name' split to 'firstName'+'lastName'" },
    { "legacy": "POST /api/users", "target": "POST /v2/users", "change": "Requires firstName+lastName" },
    { "legacy": "PUT /api/users/:id", "target": "PATCH /v2/users/:id", "change": "Full replace -> partial update" }
  ]
}
```

## Request/Response Adapters

```javascript
// migration/adapters/user-adapter.js
function adaptV1RequestToV2(body) {
  const result = { ...body };
  if (body.name) {
    const parts = body.name.split(' ');
    result.firstName = parts[0];
    result.lastName = parts.slice(1).join(' ') || '';
    delete result.name;
  }
  return result;
}

function adaptV2ResponseToV1(body) {
  const result = { ...body };
  if (body.firstName !== undefined) {
    result.name = `${body.firstName} ${body.lastName}`.trim();
    delete result.firstName;
    delete result.lastName;
  }
  return result;
}

function adaptV2ListToV1(response) {
  if (response.data) return response.data.map(adaptV2ResponseToV1);
  return response;
}
```

## Traffic Router with Phases

```javascript
// migration/router.js
const PHASE = process.env.MIGRATION_PHASE || 'shadow';

function migrationRouter(legacyHandler, targetHandler, adapter) {
  return async (req, res) => {
    switch (PHASE) {
      case 'legacy':
        return legacyHandler(req, res);

      case 'shadow': {
        const result = await legacyHandler(req, res);
        setImmediate(async () => {
          try {
            const adapted = adapter.adaptRequest(req.body);
            const targetResult = await targetHandler.execute(adapted);
            const diff = compareResponses(result, targetResult);
            if (diff.hasDifferences) logger.warn('Shadow diff', { diff });
          } catch (err) { logger.error('Shadow failed', { err: err.message }); }
        });
        return result;
      }

      case 'canary':
        if (Math.random() < 0.1) {
          const adapted = adapter.adaptRequest(req.body);
          return res.json(adapter.adaptResponse(await targetHandler.execute(adapted)));
        }
        return legacyHandler(req, res);

      case 'migrated':
        return res.json(adapter.adaptResponse(
          await targetHandler.execute(adapter.adaptRequest(req.body))
        ));
    }
  };
}
```

## Strangler Fig with nginx

```nginx
upstream legacy_api { server legacy-api:3000; }
upstream target_api { server target-api:4000; }

# Migrated endpoints
location /v2/users { proxy_pass http://target_api; }

# Legacy endpoints
location /api/ { proxy_pass http://legacy_api; }

# Canary: split traffic
split_clients $request_id $backend {
    10%  target_api;
    90%  legacy_api;
}
location /api/orders { proxy_pass http://$backend; }
```

## Migration Dashboard

```javascript
async function getMigrationStatus() {
  const endpoints = await db.query('SELECT * FROM migration_endpoints');
  return {
    summary: {
      total: endpoints.length,
      legacy: endpoints.filter(e => e.phase === 'legacy').length,
      shadow: endpoints.filter(e => e.phase === 'shadow').length,
      canary: endpoints.filter(e => e.phase === 'canary').length,
      migrated: endpoints.filter(e => e.phase === 'migrated').length,
    },
    endpoints: endpoints.map(e => ({
      path: e.path, phase: e.phase,
      shadowDiffRate: e.shadow_diff_count / e.shadow_total,
      canaryErrorRate: e.canary_error_count / e.canary_total,
    })),
  };
}
```

## Parity Test

```javascript
describe('Migration Parity', () => {
  const cases = [
    { method: 'GET', path: '/users' },
    { method: 'GET', path: '/users/1' },
    { method: 'POST', path: '/users', body: { name: 'Test User' } },
  ];
  for (const tc of cases) {
    it(`${tc.method} ${tc.path}: legacy equals target`, async () => {
      const legacy = await fetch(`http://legacy:3000${tc.path}`, {
        method: tc.method,
        body: tc.body ? JSON.stringify(tc.body) : undefined,
        headers: { 'Content-Type': 'application/json' },
      });
      const adapted = tc.body ? adaptV1RequestToV2(tc.body) : undefined;
      const target = await fetch(`http://target:4000${tc.path}`, {
        method: tc.method,
        body: adapted ? JSON.stringify(adapted) : undefined,
        headers: { 'Content-Type': 'application/json' },
      });
      expect(legacy.status).toBe(target.status);
      expect(adaptV2ResponseToV1(await target.json())).toEqual(await legacy.json());
    });
  }
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
