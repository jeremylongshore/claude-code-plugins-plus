Shopify Plus Organization API for multi-store management and access audit trail implementation.

### Organization API

```typescript
// Shopify Plus Organization features (multi-store management)
// Access via the Organization API

const ORG_STORES_QUERY = `{
  organizationStores(first: 50) {
    edges {
      node {
        id
        name
        shopDomain
        plan {
          displayName
        }
        staff(first: 10) {
          edges {
            node {
              email
              role
            }
          }
        }
      }
    }
  }
}`;

// Organization-level roles:
// - Organization admin: full access to all stores
// - Store-level admin: full access to assigned stores
// - Store-level staff: permission-based access
```

### Audit Trail for Access

```typescript
interface AccessAuditEntry {
  timestamp: Date;
  userId: string;
  userEmail: string;
  role: AppRole;
  action: string;
  resource: string;
  shopDomain: string;
  locationId?: string;
  allowed: boolean;
  ipAddress?: string;
}

async function auditAccess(entry: AccessAuditEntry): Promise<void> {
  await db.accessAudit.create({ data: entry });

  // Alert on denied access attempts
  if (!entry.allowed) {
    console.warn(
      `[ACCESS DENIED] ${entry.userEmail} attempted ${entry.action} ` +
      `on ${entry.resource} in ${entry.shopDomain}`
    );
  }
}
```
