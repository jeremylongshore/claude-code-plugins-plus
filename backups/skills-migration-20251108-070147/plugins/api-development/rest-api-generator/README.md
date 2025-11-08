# REST API Generator Plugin

Generate production-ready RESTful APIs from schema definitions with proper routing, validation, error handling, and documentation.

## Installation

```bash
/plugin install rest-api-generator@claude-code-plugins-plus
```

## Usage

### Basic Usage

```bash
/generate-rest-api
```

Or use the shortcut:

```bash
/gra
```

### What It Does

1. Asks about your API requirements (resources, operations, framework)
2. Generates complete REST API structure with routes, controllers, models
3. Adds validation schemas with Joi, Pydantic, or Zod
4. Implements authentication middleware (JWT, OAuth, API keys)
5. Creates OpenAPI/Swagger documentation
6. Generates integration tests for all endpoints
7. Follows REST best practices (proper HTTP methods, status codes, pagination)

### Example Interaction

```
You: /generate-rest-api

Claude: I'll help you generate a RESTful API. Let me gather some details:

1. What resources/entities do you need? (e.g., users, posts, products)
2. What framework would you like? (Express, FastAPI, Django, Flask, NestJS)
3. What database? (PostgreSQL, MongoDB, MySQL)
4. Do you need authentication? (JWT, OAuth, API keys)

You: Users and posts, Express with PostgreSQL, JWT auth

Claude: [Generates complete API structure with routes, controllers, models, validation, tests, and OpenAPI docs]
```

## Generated API Structure

```
api/
├── routes/               # RESTful endpoints
├── controllers/          # Business logic
├── models/              # Data models
├── middleware/          # Auth, validation, rate limiting
├── schemas/             # Validation schemas
├── tests/               # Integration tests
├── docs/                # OpenAPI documentation
└── server.js            # Entry point
```

## Features

- **REST Principles** - Resource-based URLs, proper HTTP methods
- **Validation** - Request body, query params, path params
- **Authentication** - JWT, OAuth, API key support
- **Documentation** - OpenAPI 3.0 specification
- **Testing** - Integration tests with Jest/Pytest
- **Pagination** - Limit, offset, cursor-based
- **Filtering** - Query parameter filtering
- **Sorting** - Multi-field sorting
- **Rate Limiting** - Prevent API abuse
- **CORS** - Cross-origin support
- **Error Handling** - Standardized error responses

## Supported Frameworks

- **Node.js**: Express, NestJS, Fastify
- **Python**: FastAPI, Django REST Framework, Flask
- **Go**: Gin, Echo
- **Ruby**: Rails API, Sinatra

## Best Practices

- Proper HTTP status codes (200, 201, 400, 404, 500)
- API versioning (`/v1/`, `/v2/`)
- Input validation on all endpoints
- Consistent error response format
- Comprehensive OpenAPI documentation
- Security headers (CORS, CSP, HSTS)
- Rate limiting and throttling
- Request/response logging

## Requirements

- Node.js 18+ (for Express/NestJS)
- Python 3.9+ (for FastAPI/Django)
- Database (PostgreSQL, MongoDB, MySQL)

## License

MIT
