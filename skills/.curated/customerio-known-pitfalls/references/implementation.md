# Customer.io Known Pitfalls - Implementation Details

## Configuration

### Anti-Pattern Detection Script

```typescript
interface PitfallCheck {
  name: string;
  severity: 'critical' | 'warning' | 'info';
  check: () => Promise<boolean>;
  fix: string;
}

const PITFALL_CHECKS: PitfallCheck[] = [
  {
    name: 'unscoped_identify_calls',
    severity: 'critical',
    check: async () => {
      // Check if identify calls include customer_id
      return !hasProperIdentification();
    },
    fix: 'Always include a stable customer_id, not just email',
  },
  {
    name: 'missing_event_deduplication',
    severity: 'warning',
    check: async () => !hasEventDeduplication(),
    fix: 'Add idempotency keys to track() calls to prevent duplicate events',
  },
  {
    name: 'oversized_attributes',
    severity: 'warning',
    check: async () => {
      const attrs = await getAverageAttributeSize();
      return attrs > 10000; // bytes
    },
    fix: 'Keep person attributes under 10KB; move large data to events',
  },
  {
    name: 'no_error_handling_on_track',
    severity: 'critical',
    check: async () => !hasTrackErrorHandling(),
    fix: 'Wrap all cio.track() calls in try/catch with retry logic',
  },
];
```

## Advanced Patterns

### Pitfall: Identify Before Track Race Condition

```typescript
// BAD: Race condition - track may arrive before identify
cio.identify(userId, { email, name });
cio.track(userId, { name: 'signup_completed' });

// GOOD: Ensure identify completes first
await cio.identify(userId, { email, name });
await cio.track(userId, { name: 'signup_completed' });

// BEST: Use a queue to guarantee ordering
const queue = new CustomerIOQueue();
queue.enqueue({ type: 'identify', userId, data: { email, name } });
queue.enqueue({ type: 'track', userId, event: 'signup_completed' });
await queue.flush(); // processes in order
```

### Pitfall: Attribute Explosion

```typescript
// BAD: Dynamic attribute names create schema explosion
cio.identify(userId, {
  [`last_viewed_product_${productId}`]: timestamp,
  // Creates thousands of unique attributes
});

// GOOD: Use events for dynamic data
cio.track(userId, {
  name: 'product_viewed',
  data: { product_id: productId, timestamp },
});
```

### Pitfall: Not Handling Anonymous to Identified Merge

```typescript
// BAD: Loses anonymous browsing history
function onLogin(userId: string) {
  cio.identify(userId, { email });
}

// GOOD: Merge anonymous profile into identified profile
function onLogin(userId: string, anonymousId: string) {
  cio.mergeCustomers('cio_id', anonymousId, {
    primary: { id: userId, email },
  });
}
```

### Pitfall: Timezone-Unaware Timestamps

```typescript
// BAD: Local time without timezone
cio.track(userId, {
  name: 'purchase',
  data: { purchased_at: new Date().toString() },
});

// GOOD: Always use Unix timestamps (Customer.io native format)
cio.track(userId, {
  name: 'purchase',
  data: { purchased_at: Math.floor(Date.now() / 1000) },
});
```

## Troubleshooting

### Diagnosing Silent Data Loss

```bash
# Check Customer.io activity log for a specific person
curl -s -H "Authorization: Bearer $CIO_APP_API_KEY" \
  "https://api.customer.io/v1/customers/$CUSTOMER_ID/activities" | \
  jq '.activities[:5] | .[] | {type, timestamp, data}'

# Compare sent events vs received
echo "Sent events (from your logs): $(grep "cio.track" app.log | wc -l)"
echo "Received events (API): $(curl -s ... | jq '.activities | length')"
```

### Verifying Attribute Limits

```bash
# Check attribute size for a customer
curl -s -H "Authorization: Bearer $CIO_APP_API_KEY" \
  "https://api.customer.io/v1/customers/$CUSTOMER_ID/attributes" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Attributes: {len(d)}, Size: {len(json.dumps(d))} bytes')"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
