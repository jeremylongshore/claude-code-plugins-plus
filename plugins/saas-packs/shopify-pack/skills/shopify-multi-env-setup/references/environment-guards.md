# Environment Guards

Safety functions to prevent dangerous operations from running in the wrong environment.

```typescript
// Prevent dangerous operations outside production
function requireProduction(operation: string): void {
  if (process.env.NODE_ENV !== "production") {
    console.log(`[DEV] ${operation} — would execute in production`);
    return;
  }
}

function blockInProduction(operation: string): void {
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      `Operation "${operation}" is blocked in production. ` +
      `Use staging or development environment.`
    );
  }
}

// Example: prevent test data seeding in production
async function seedTestProducts() {
  blockInProduction("seedTestProducts");
  // ... seeding logic
}

// Example: ensure billing only runs in production
async function activateBilling(session: Session) {
  requireProduction("activateBilling");
  // ... billing logic
}
```
