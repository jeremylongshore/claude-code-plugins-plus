# Implementation Guide

### Step 1: Design API Structure
Plan the API architecture and endpoints:
1. Use Read tool to examine existing API specifications from ${CLAUDE_SKILL_DIR}/api-specs/
2. Define resource models, endpoints, and HTTP methods
3. Document request/response schemas and data types
4. Identify authentication and authorization requirements
5. Plan error handling and validation strategies

### Step 2: Implement API Components
Build the API implementation:
1. Generate boilerplate code using Bash(api:websocket-*) with framework scaffolding
2. Implement endpoint handlers with business logic
3. Add input validation and schema enforcement
4. Integrate authentication and authorization middleware
5. Configure database connections and ORM models

### Step 3: Add API Features
Enhance with production-ready capabilities:
- Implement rate limiting and throttling policies
- Add request/response logging with correlation IDs
- Configure error handling with standardized responses
- Set up health check and monitoring endpoints
- Enable CORS and security headers

### Step 4: Test and Document
Validate API functionality:
1. Write integration tests covering all endpoints
2. Generate OpenAPI/Swagger documentation automatically
3. Create usage examples and authentication guides
4. Test with various HTTP clients (curl, Postman, REST Client)
5. Perform load testing to validate performance targets