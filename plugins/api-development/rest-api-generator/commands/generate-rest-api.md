---
description: Generate a RESTful API from a schema definition
shortcut: gra
---

# Generate REST API

Generate a complete RESTful API implementation from a schema definition with proper routing, validation, error handling, and documentation.

## What You Do

1. **Ask for schema details:**
   - What resources/entities? (e.g., users, posts, products)
   - What operations? (CRUD, custom endpoints)
   - What framework? (Express, FastAPI, Django, Flask, NestJS)
   - What database? (PostgreSQL, MongoDB, MySQL)
   - Authentication needed? (JWT, OAuth, API keys)

2. **Generate comprehensive API structure:**
   - **Routes/Controllers** - RESTful endpoints with proper HTTP methods
   - **Models/Schemas** - Data validation with Joi, Pydantic, Zod
   - **Middleware** - Authentication, rate limiting, CORS
   - **Error handling** - Standardized error responses
   - **OpenAPI/Swagger docs** - Auto-generated documentation
   - **Tests** - Integration tests for all endpoints

3. **Follow REST best practices:**
   - Use proper HTTP status codes (200, 201, 400, 404, 500)
   - Implement HATEOAS links where appropriate
   - Support pagination with `limit`, `offset`, `cursor`
   - Enable filtering, sorting, searching with query params
   - Version APIs properly (`/v1/`, `/v2/`)
   - Use proper HTTP methods (GET, POST, PUT, PATCH, DELETE)

4. **Generate validation:**
   - Request body validation
   - Query parameter validation
   - Path parameter validation
   - Custom business logic validation

5. **Create documentation:**
   - OpenAPI 3.0 specification
   - README with setup instructions
   - Example requests with curl/httpie
   - Postman collection export

## Example Structure

```
api/
├── routes/
│   ├── users.js       # /api/users endpoints
│   ├── posts.js       # /api/posts endpoints
│   └── index.js       # Route aggregator
├── controllers/
│   ├── users.js       # Business logic
│   └── posts.js
├── models/
│   ├── User.js        # Data models
│   └── Post.js
├── middleware/
│   ├── auth.js        # JWT validation
│   ├── validate.js    # Request validation
│   └── rateLimit.js   # Rate limiting
├── schemas/
│   ├── user.schema.js # Validation schemas
│   └── post.schema.js
├── tests/
│   ├── users.test.js  # Integration tests
│   └── posts.test.js
├── docs/
│   └── openapi.yaml   # API documentation
├── app.js             # Express app setup
└── server.js          # Server entry point
```

## Key Features to Include

- **Resource-based URLs** - `/api/users`, `/api/users/:id`
- **HTTP methods** - GET (read), POST (create), PUT (full update), PATCH (partial), DELETE
- **Status codes** - 200 OK, 201 Created, 204 No Content, 400 Bad Request, 404 Not Found, 500 Error
- **Pagination** - `GET /api/users?limit=10&offset=20`
- **Filtering** - `GET /api/users?role=admin&active=true`
- **Sorting** - `GET /api/users?sort=createdAt&order=desc`
- **Searching** - `GET /api/users?search=john`
- **Field selection** - `GET /api/users?fields=id,name,email`
- **Authentication** - JWT tokens, API keys
- **Rate limiting** - Prevent API abuse
- **CORS** - Cross-origin resource sharing
- **Error handling** - Consistent error format
- **Logging** - Request/response logging

Always generate production-ready, well-documented APIs following REST principles and industry best practices.
