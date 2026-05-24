# Examples

## Example 1: Complete CRUD Contract for a Resource

A full api-contract.md covering all standard CRUD operations for a single
resource with typed request/response schemas and error codes.

```markdown
# API Contract: Products

## Shared Types

### Product
| Field       | Type              | Description                    |
|-------------|-------------------|--------------------------------|
| id          | uuid              | Unique product identifier      |
| name        | string (required) | Product name, 1-200 chars      |
| description | string (optional) | Product description, max 5000  |
| price       | number (required) | Price in cents (integer)       |
| category    | string (required) | One of: electronics, clothing, food, other |
| inStock     | boolean           | Availability flag              |
| createdAt   | ISO 8601 datetime | Creation timestamp             |
| updatedAt   | ISO 8601 datetime | Last modification timestamp    |

### ApiError
| Field   | Type                       | Description              |
|---------|----------------------------|--------------------------|
| code    | string                     | Machine-readable error   |
| message | string                     | Human-readable message   |
| details | Record<string, string[]>?  | Field-level errors       |

---

#### POST /api/products

Create a new product.

**Request:**
| Field       | Type   | Required | Constraints                |
|-------------|--------|----------|----------------------------|
| name        | string | yes      | 1-200 characters           |
| description | string | no       | Max 5000 characters        |
| price       | number | yes      | Integer, >= 0 (cents)      |
| category    | string | yes      | electronics, clothing, food, other |

**Response (201 Created):**
Returns the full Product object with generated id, createdAt, updatedAt.

**Errors:**
- 400: Missing required fields → `{ code: "VALIDATION_ERROR", details: { name: ["required"] } }`
- 422: Price is negative → `{ code: "INVALID_PRICE", message: "Price must be >= 0" }`

---

#### GET /api/products/:id

Retrieve a single product by ID.

**Path Parameters:**
| Param | Type | Description           |
|-------|------|-----------------------|
| id    | uuid | Product identifier    |

**Response (200 OK):**
Returns the full Product object.

**Errors:**
- 404: Product not found → `{ code: "NOT_FOUND", message: "Product not found" }`

---

#### PATCH /api/products/:id

Update one or more product fields. Only provided fields are modified.

**Request:**
| Field       | Type   | Required | Constraints           |
|-------------|--------|----------|-----------------------|
| name        | string | no       | 1-200 characters      |
| description | string | no       | Max 5000 characters   |
| price       | number | no       | Integer, >= 0 (cents) |
| category    | string | no       | Valid category value   |

**Response (200 OK):**
Returns the updated Product object with new updatedAt timestamp.

**Errors:**
- 400: Invalid field value → field-level details
- 404: Product not found
- 409: Concurrent modification → `{ code: "CONFLICT", message: "Product was modified" }`

---

#### DELETE /api/products/:id

Soft-delete a product (sets archived flag, does not remove from database).

**Response (204 No Content):**
Empty body on success.

**Errors:**
- 404: Product not found
- 409: Product already archived

---

#### GET /api/products

List products with pagination and filtering.

**Query Parameters:**
| Param    | Type    | Default   | Description                       |
|----------|---------|-----------|-----------------------------------|
| page     | integer | 1         | Page number (1-based)             |
| limit    | integer | 20        | Items per page (max 100)          |
| sort     | string  | createdAt | Sort field (name, price, createdAt) |
| order    | string  | desc      | Sort direction (asc, desc)        |
| category | string  | (all)     | Filter by category                |
| inStock  | boolean | (all)     | Filter by availability            |

**Response (200 OK):**
```json
{
  "data": [Product],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8
  }
}
```

**Errors:**

- 400: Invalid query parameter → `{ code: "INVALID_PARAM", details: { limit: ["max 100"] } }`

```

## Example 2: Authentication Contract with Token Flow

A contract covering registration, login, and token refresh with explicit
security considerations.

```markdown
# API Contract: Authentication

## Shared Types

### AuthTokens
| Field        | Type   | Description                           |
|--------------|--------|---------------------------------------|
| accessToken  | string | JWT, 15-minute expiry, HS256          |
| refreshToken | string | Opaque token, 7-day expiry, stored DB |
| expiresIn    | number | Access token TTL in seconds (900)     |

### UserProfile
| Field       | Type              | Description                    |
|-------------|-------------------|--------------------------------|
| id          | uuid              | User identifier                |
| email       | string            | Verified email address         |
| name        | string or null    | Display name (optional)        |
| role        | string            | One of: user, admin            |
| createdAt   | ISO 8601 datetime | Registration timestamp         |

---

#### POST /auth/register

Create a new user account and return authentication tokens.

**Request:**
| Field    | Type   | Required | Constraints                     |
|----------|--------|----------|---------------------------------|
| email    | string | yes      | Valid email format, max 254     |
| password | string | yes      | Min 8 chars, at least 1 number  |
| name     | string | no       | 1-100 characters                |

**Response (201 Created):**
```json
{
  "user": UserProfile,
  "tokens": AuthTokens
}
```

**Errors:**

- 400: Invalid email format or weak password → field-level details
- 409: Email already registered → `{ code: "EMAIL_EXISTS" }`

---

### POST /auth/login

Authenticate with email and password.

**Request:**

| Field    | Type   | Required |
|----------|--------|----------|
| email    | string | yes      |
| password | string | yes      |

**Response (200 OK):**

```json
{
  "user": UserProfile,
  "tokens": AuthTokens
}
```

**Errors:**

- 401: Invalid credentials → `{ code: "INVALID_CREDENTIALS" }`
  (same message for wrong email and wrong password to prevent enumeration)
- 429: Too many attempts → `{ code: "RATE_LIMITED", message: "Try again in 60s" }`

---

#### POST /auth/refresh

Exchange a valid refresh token for new tokens. The old refresh token is
invalidated (rotation).

**Request:**

| Field        | Type   | Required |
|--------------|--------|----------|
| refreshToken | string | yes      |

**Response (200 OK):**

```json
{
  "tokens": AuthTokens
}
```

**Errors:**

- 401: Invalid or expired refresh token → `{ code: "INVALID_REFRESH_TOKEN" }`
  (also triggered if token was already rotated — potential theft detection)

---

#### POST /auth/logout

Invalidate the refresh token for the current session.

**Headers:**

| Header        | Value                |
|---------------|----------------------|
| Authorization | Bearer {accessToken} |

**Request:**

| Field        | Type   | Required |
|--------------|--------|----------|
| refreshToken | string | yes      |

**Response (204 No Content):**
Empty body.

**Errors:**

- 401: Missing or invalid access token

```

## Example 3: TypeScript Interface Definitions

Canonical type definitions shared between backend and frontend agents.

```typescript
// types/api.ts — Shared types for api-contract.md

/** Standard paginated response wrapper */
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

/** Standard API error response */
interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string[]>;
}

/** Product resource */
interface Product {
  id: string;
  name: string;
  description: string | null;
  price: number;           // in cents
  category: 'electronics' | 'clothing' | 'food' | 'other';
  inStock: boolean;
  createdAt: string;       // ISO 8601
  updatedAt: string;       // ISO 8601
}

/** Create product request body */
interface CreateProductRequest {
  name: string;
  description?: string;
  price: number;
  category: Product['category'];
}

/** Update product request body (all fields optional) */
interface UpdateProductRequest {
  name?: string;
  description?: string;
  price?: number;
  category?: Product['category'];
}

/** Search request with filters */
interface SearchRequest {
  query: string;
  filters?: {
    category?: Product['category'];
    priceMin?: number;
    priceMax?: number;
    inStock?: boolean;
  };
  page?: number;
  limit?: number;
}

/** Search response with facets */
interface SearchResponse {
  results: Product[];
  total: number;
  facets: FacetGroup[];
}

/** Facet group for filtering */
interface FacetGroup {
  name: string;
  values: Array<{
    value: string;
    count: number;
  }>;
}
```

## Example 4: Contract with Nested Resources

An API contract where one resource is nested under another, showing
the relationship between parent and child endpoints.

```markdown
# API Contract: Orders and Line Items

## Shared Types

### Order
| Field     | Type              | Description                    |
|-----------|-------------------|--------------------------------|
| id        | uuid              | Order identifier               |
| userId    | uuid              | Customer identifier            |
| status    | string            | pending, confirmed, shipped, delivered, cancelled |
| total     | number            | Total in cents                 |
| items     | LineItem[]        | Ordered products               |
| createdAt | ISO 8601 datetime | Order creation time            |

### LineItem
| Field     | Type   | Description                    |
|-----------|--------|--------------------------------|
| productId | uuid   | Product reference              |
| name      | string | Product name at time of order  |
| quantity  | number | Integer, >= 1                  |
| unitPrice | number | Price in cents at time of order |
| subtotal  | number | quantity * unitPrice           |

---

#### POST /api/orders

Create a new order from the user's cart.

**Headers:**
Authorization: Bearer {accessToken}

**Request:**
| Field | Type                                  | Required |
|-------|---------------------------------------|----------|
| items | Array<{ productId: uuid, quantity: number }> | yes |

**Response (201 Created):**
Returns the full Order object with computed totals and line items.

**Errors:**
- 400: Empty items array → `{ code: "EMPTY_CART" }`
- 404: Product not found → `{ code: "PRODUCT_NOT_FOUND", details: { productId: ["..."] } }`
- 409: Product out of stock → `{ code: "OUT_OF_STOCK", details: { productId: ["..."] } }`
- 422: Quantity exceeds available stock

---

#### GET /api/orders/:orderId/items

List line items for a specific order.

**Response (200 OK):**
```json
{
  "data": [LineItem],
  "orderId": "uuid",
  "itemCount": 3
}
```

**Errors:**

- 403: Order belongs to a different user
- 404: Order not found

```

## Example 5: Contract Section for Webhook Callbacks

When the API needs to send callbacks to external systems, the contract
documents the outbound payload format.

```markdown
# Webhook Events

## Order Status Changed

Sent when an order transitions between statuses.

**POST {webhookUrl}**

**Payload:**
| Field      | Type              | Description                    |
|------------|-------------------|--------------------------------|
| event      | string            | Always "order.status.changed"  |
| orderId    | uuid              | Order identifier               |
| oldStatus  | string            | Previous status value          |
| newStatus  | string            | New status value               |
| timestamp  | ISO 8601 datetime | When the transition occurred   |
| metadata   | object (optional) | Additional context (tracking number, carrier) |

**Expected Response:**
- 200 OK: Webhook processed successfully
- 4xx/5xx: Retry with exponential backoff (3 attempts, 30s/120s/300s delays)

**Signature Header:**
X-Webhook-Signature: HMAC-SHA256 of the JSON body using the shared secret
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
