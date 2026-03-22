---
name: shopify-enterprise-rbac
description: |
  Implement Shopify Plus access control patterns with staff permissions,
  multi-location management, and Shopify Organization features.
  Trigger with phrases like "shopify permissions", "shopify staff",
  "shopify Plus organization", "shopify roles", "shopify multi-location".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Enterprise RBAC

## Overview

Implement role-based access control for Shopify Plus apps using Shopify's staff member permissions, multi-location features, and Organization-level access.

## Prerequisites

- Shopify Plus store (for Organization features)
- Understanding of Shopify's staff permission model
- `read_users` scope for querying staff permissions

## Instructions

### Step 1: Query Staff Member Permissions

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

### Step 2: App-Level Role Mapping

Map Shopify staff permissions to your app's roles:

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

### Step 3: Embedded App Permission Middleware

```typescript
// In an embedded Shopify app, the session token contains the staff member info
import { authenticate } from "../shopify.server";

// Remix loader with permission check
export async function loader({ request }: LoaderFunctionArgs) {
  const { admin, session } = await authenticate.admin(request);

  // session.onlineAccessInfo contains staff permissions for online tokens
  const staffInfo = session.onlineAccessInfo;
  if (!staffInfo) {
    // Offline token — no per-user permissions available
    return json({ role: "admin" });
  }

  const scopes = staffInfo.associated_user_scope.split(",");
  const role = determineRole(scopes);

  // Check permission for this specific page
  if (!canPerformAction(role, "view_orders")) {
    throw new Response("Forbidden", { status: 403 });
  }

  return json({ role, user: staffInfo.associated_user });
}
```

### Step 4: Multi-Location Access Control

```typescript
// Shopify Plus stores can have multiple locations
// Control which locations a staff member can access

const LOCATIONS_QUERY = `{
  locations(first: 50) {
    edges {
      node {
        id
        name
        isActive
        address {
          city
          province
          country
        }
        fulfillmentService {
          serviceName
        }
      }
    }
  }
}`;

// Restrict operations to authorized locations
interface LocationPermission {
  locationId: string;
  canFulfill: boolean;
  canAdjustInventory: boolean;
  canViewOrders: boolean;
}

async function checkLocationAccess(
  userId: string,
  locationId: string,
  action: "fulfill" | "adjust_inventory" | "view_orders"
): Promise<boolean> {
  const permissions = await db.locationPermissions.findFirst({
    where: { userId, locationId },
  });

  if (!permissions) return false;

  switch (action) {
    case "fulfill": return permissions.canFulfill;
    case "adjust_inventory": return permissions.canAdjustInventory;
    case "view_orders": return permissions.canViewOrders;
    default: return false;
  }
}
```

### Step 5: Shopify Plus Organization API

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

### Step 6: Audit Trail for Access

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

## Output

- Staff permissions queried and mapped to app roles
- Permission middleware protecting embedded app routes
- Multi-location access control for Shopify Plus
- Audit trail for all access decisions

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| No `onlineAccessInfo` | Using offline token | Use online access tokens for per-user permissions |
| Staff can't access feature | Merchant restricted their permissions | Staff must request access from store owner |
| Organization API 403 | Not on Shopify Plus | Organization features require Plus plan |
| Location not found | Location deactivated | Query active locations before operations |

## Examples

### Quick Permission Check in Remix

```typescript
// Remix action with permission guard
export async function action({ request }: ActionFunctionArgs) {
  const { admin, session } = await authenticate.admin(request);

  const role = determineRole(
    session.onlineAccessInfo?.associated_user_scope?.split(",") || []
  );

  if (!canPerformAction(role, "manage_products")) {
    return json({ error: "Insufficient permissions" }, { status: 403 });
  }

  // ... perform the action
}
```

## Resources

- [Shopify Staff Permissions](https://help.shopify.com/en/manual/your-account/staff-accounts/staff-permissions)
- [Online vs Offline Tokens](https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens)
- [Shopify Plus Organization](https://help.shopify.com/en/manual/shopify-plus/organization)
- [Multi-Location Inventory](https://shopify.dev/docs/apps/build/orders-fulfillment/inventory-management-apps)

## Next Steps

For major migrations, see `shopify-migration-deep-dive`.
