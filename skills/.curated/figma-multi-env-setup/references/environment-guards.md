# Step 5: Environment Guards

Deep-dive reference for the `figma-multi-env-setup` skill — extracted from the 'Step 5: Environment Guards' step of the workflow.

```typescript
// Prevent production-specific operations in non-production
function requireProduction(operation: string) {
  if (process.env.NODE_ENV !== 'production') {
    throw new Error(
      `${operation} is only allowed in production. ` +
      `Current env: ${process.env.NODE_ENV}`
    );
  }
}

// Prevent destructive operations in production
function blockInProduction(operation: string) {
  if (process.env.NODE_ENV === 'production') {
    throw new Error(`${operation} is blocked in production for safety`);
  }
}

// Usage
async function createWebhook(config: any) {
  requireProduction('createWebhook'); // Only in prod
  return fetch('https://api.figma.com/v2/webhooks', { ... });
}

async function deleteAllCachedData() {
  blockInProduction('deleteAllCachedData'); // Never in prod
  await cache.clear();
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
