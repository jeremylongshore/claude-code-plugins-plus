# Post-Migration Validation

Automated validation script that compares expected source counts against actual Shopify counts to verify migration completeness.

```typescript
async function validateMigration(expectedCounts: Record<string, number>): Promise<void> {
  const checks = [
    {
      name: "Products",
      query: "{ productsCount { count } }",
      path: "productsCount.count",
      expected: expectedCounts.products,
    },
    {
      name: "Customers",
      query: "{ customersCount { count } }",
      path: "customersCount.count",
      expected: expectedCounts.customers,
    },
  ];

  for (const check of checks) {
    const response = await client.request(check.query);
    const actual = check.path.split(".").reduce((obj: any, k) => obj[k], response.data);
    const status = actual >= check.expected ? "PASS" : "FAIL";
    console.log(`${status}: ${check.name} — expected ${check.expected}, got ${actual}`);
  }
}
```
