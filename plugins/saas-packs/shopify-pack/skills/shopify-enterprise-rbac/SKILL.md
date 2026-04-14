---
name: shopify-enterprise-rbac
description: |
  Implement Shopify Plus access control patterns with staff permissions,
  multi-location management, and Shopify Organization features.
  Use when building apps for Shopify Plus merchants, implementing per-staff permissions, or managing multi-store organizations.
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

### Step 1: Query Staff Permissions and Map to App Roles

Query staff members via GraphQL to get their access scopes, then map those scopes to app-level roles (admin, manager, fulfillment, viewer). Staff permissions mirror app scopes like `read_products`, `write_orders`, etc.

See [Staff Query and Role Mapping](references/staff-query-and-role-mapping.md) for the complete GraphQL query, role definitions, and matching logic.

### Step 2: Permission Middleware and Multi-Location Access

In embedded apps, use online access tokens to get per-staff permissions from `session.onlineAccessInfo`. For Shopify Plus stores with multiple locations, restrict fulfillment and inventory operations to authorized locations per user.

See [Permission Middleware and Location Access](references/permission-middleware-and-location-access.md) for Remix loader examples and location access control.

### Step 3: Organization API and Audit Trail

Shopify Plus Organization API enables multi-store management with organization-level, store-level admin, and store-level staff roles. Log all access decisions (allowed and denied) for compliance auditing.

See [Organization API and Audit Trail](references/organization-api-and-audit-trail.md) for the Organization query and audit implementation.

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
