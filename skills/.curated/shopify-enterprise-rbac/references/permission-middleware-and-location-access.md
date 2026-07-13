Embedded app permission middleware for Remix loaders and multi-location access control for Shopify Plus stores.

### Embedded App Permission Middleware

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

### Multi-Location Access Control

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
