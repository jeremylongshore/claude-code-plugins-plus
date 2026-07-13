Query staff member permissions via GraphQL and map them to application-level roles.

### Staff Member Query

```typescript
// Query staff members and their permissions via GraphQL
const STAFF_QUERY = `{
  staffMembers(first: 50) {
    edges {
      node {
        id
        email
        firstName
        lastName
        isShopOwner
        active
        locale
        permissions: accessScopes {
          handle
          description
        }
      }
    }
  }
}`;

// Staff permissions match app access scopes:
// "read_products", "write_products", "read_orders", etc.
// A staff member can only use app features matching their store permissions
```

### App-Level Role Mapping

```typescript
type AppRole = "admin" | "manager" | "viewer" | "fulfillment";

interface RoleMapping {
  role: AppRole;
  requiredScopes: string[];
  allowedActions: string[];
}

const ROLE_MAPPINGS: RoleMapping[] = [
  {
    role: "admin",
    requiredScopes: ["write_products", "write_orders", "write_customers"],
    allowedActions: ["*"],
  },
  {
    role: "manager",
    requiredScopes: ["write_products", "read_orders"],
    allowedActions: ["manage_products", "view_orders", "view_analytics"],
  },
  {
    role: "fulfillment",
    requiredScopes: ["read_orders", "write_fulfillments"],
    allowedActions: ["view_orders", "create_fulfillment", "update_tracking"],
  },
  {
    role: "viewer",
    requiredScopes: ["read_products"],
    allowedActions: ["view_products", "view_analytics"],
  },
];

function determineRole(staffScopes: string[]): AppRole {
  // Find the highest-privilege role the staff member qualifies for
  for (const mapping of ROLE_MAPPINGS) {
    if (mapping.requiredScopes.every((s) => staffScopes.includes(s))) {
      return mapping.role;
    }
  }
  return "viewer"; // fallback
}

function canPerformAction(role: AppRole, action: string): boolean {
  const mapping = ROLE_MAPPINGS.find((m) => m.role === role);
  if (!mapping) return false;
  return mapping.allowedActions.includes("*") || mapping.allowedActions.includes(action);
}
```
