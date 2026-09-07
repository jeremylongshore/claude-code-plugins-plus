# Klaviyo SDK Patterns — Worked Examples

End-to-end examples that combine the helpers from
[implementation.md](implementation.md). Each shows the expected shape of the
result so you know what a correct run looks like.

## Example 1: Safe single call with typed error

Wrap any API operation with `safeCall` to get a `{ data, error }` result
instead of a thrown exception.

```typescript
import apis from './klaviyo/api';
import { safeCall } from './klaviyo/errors';

const { data, error } = await safeCall(
  () => apis.profiles.getProfiles({ pageSize: 20 }),
  'list profiles',
);

if (error) {
  // error is a typed KlaviyoApiError
  console.error(`Failed (${error.status}):`, error.errors[0].detail);
} else {
  console.log(`Fetched ${data!.body.data.length} profiles`);
}
```

Expected result shape:

```jsonc
// success -> { data: <ApiResponse>, error: null }
// failure -> { data: null, error: { status: 401, errors: [...], retryAfter: undefined } }
```

## Example 2: Retry a rate-limited write

`withRetry` only retries on `429` and `5xx`, and honors the `Retry-After`
header Klaviyo returns.

```typescript
import apis from './klaviyo/api';
import { withRetry } from './klaviyo/retry';

const created = await withRetry(() =>
  apis.profiles.createProfile({
    data: {
      type: 'profile',
      attributes: { email: 'user@example.com', firstName: 'Ada' },
    },
  }),
);

console.log('Created profile id:', created.body.data.id);
```

Console output on a throttled attempt:

```text
[Klaviyo] Retry 1/3 in 2000ms   // waited exactly Retry-After seconds
```

## Example 3: Iterate every profile with pagination

`paginate` turns any cursor-based list endpoint into an async iterator, so you
never hand-manage `page[cursor]`.

```typescript
import apis from './klaviyo/api';
import { paginate } from './klaviyo/pagination';

let count = 0;
for await (const profile of paginate(cursor =>
  apis.profiles.getProfiles({ pageCursor: cursor }),
)) {
  count++;
  console.log(profile.attributes.email);
}
console.log(`Walked ${count} profiles across all pages`);
```

## Example 4: Serve two tenants from one process

`getApisForTenant` caches one client set per tenant id, so a multi-tenant
worker keeps each customer's API key isolated.

```typescript
import { getApisForTenant } from './klaviyo/multi-tenant';

const acme = getApisForTenant('acme', process.env.ACME_KLAVIYO_KEY!);
const globex = getApisForTenant('globex', process.env.GLOBEX_KLAVIYO_KEY!);

// Each call uses that tenant's own session/API key
await acme.events.createEvent({ /* ... */ });
await globex.events.createEvent({ /* ... */ });
```
