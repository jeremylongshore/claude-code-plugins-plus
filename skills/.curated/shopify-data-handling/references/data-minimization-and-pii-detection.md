GraphQL data minimization patterns and PII detection/redaction middleware for Shopify apps.

### Data Minimization in API Queries

```typescript
// BAD: Fetching all customer fields when you only need the name
const ALL_FIELDS = `{
  customer(id: $id) {
    id firstName lastName email phone
    addresses { address1 city province country zip phone }
    orders(first: 100) {
      edges { node { id name totalPrice shippingAddress { ... } } }
    }
    metafields(first: 20) { edges { node { key value } } }
  }
}`;

// GOOD: Only fetch what you actually use
const MINIMAL_FIELDS = `{
  customer(id: $id) {
    id
    displayName
    numberOfOrders
    amountSpent { amount currencyCode }
  }
}`;
```

### PII Detection in Logs

```typescript
// Prevent customer PII from leaking into logs
const PII_PATTERNS = [
  { name: "email", pattern: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { name: "phone", pattern: /\+?\d{10,15}/g },
  { name: "credit_card", pattern: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g },
];

function redactPII(text: string): string {
  let result = text;
  for (const { name, pattern } of PII_PATTERNS) {
    result = result.replace(pattern, `[REDACTED:${name}]`);
  }
  return result;
}

// Use in logging middleware
function safeLog(message: string, data: any): void {
  const safeData = JSON.parse(redactPII(JSON.stringify(data)));
  console.log(message, safeData);
}
```
