---
name: throttling-apis
description: |
  Manage API throttling policies to protect backend services from overload.
  Use when controlling API request rates.
  Trigger with phrases like "throttle API", "control request rate", or "add throttling".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(api:throttle-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure you have:
- API design specifications or requirements documented
- Development environment with necessary frameworks installed
- Database or backend services accessible for integration
- Authentication and authorization strategies defined
- Testing tools and environments configured

## Instructions

### Step 1: Design API Structure
Plan the API architecture and endpoints:
1. Use Read tool to examine existing API specifications from {baseDir}/api-specs/
2. Define resource models, endpoints, and HTTP methods
3. Document request/response schemas and data types
4. Identify authentication and authorization requirements
5. Plan error handling and validation strategies

### Step 2: Implement API Components
Build the API implementation:
1. Generate boilerplate code using Bash(api:throttle-*) with framework scaffolding
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

## Output

The skill generates production-ready API artifacts:

### API Implementation
Generated code structure:
- `{baseDir}/src/routes/` - Endpoint route definitions
- `{baseDir}/src/controllers/` - Business logic handlers
- `{baseDir}/src/models/` - Data models and schemas
- `{baseDir}/src/middleware/` - Authentication, validation, logging
- `{baseDir}/src/config/` - Configuration and environment variables

### API Documentation
Comprehensive API docs including:
- OpenAPI 3.0 specification with complete endpoint definitions
- Authentication and authorization flow diagrams
- Request/response examples for all endpoints
- Error code reference with troubleshooting guidance
- SDK generation instructions for multiple languages

### Testing Artifacts
Complete test suite:
- Unit tests for individual controller functions
- Integration tests for end-to-end API workflows
- Load test scripts for performance validation
- Mock data generators for realistic testing
- Postman/Insomnia collection for manual testing

### Configuration Files
Production-ready configs:
- Environment variable templates (.env.example)
- Database migration scripts
- Docker Compose for local development
- CI/CD pipeline configuration
- Monitoring and alerting setup

## Error Handling

Common issues and solutions:

**Schema Validation Failures**
- Error: Request body does not match expected schema
- Solution: Add detailed validation error messages; provide schema documentation; implement request sanitization

**Authentication Errors**
- Error: Invalid or expired authentication tokens
- Solution: Implement proper token refresh flows; add clear error messages indicating auth failure reason; document token lifecycle

**Rate Limit Exceeded**
- Error: API consumer exceeded allowed request rate
- Solution: Return 429 status with Retry-After header; implement exponential backoff guidance; provide rate limit info in response headers

**Database Connection Issues**
- Error: Cannot connect to database or query timeout
- Solution: Implement connection pooling; add health checks; configure proper timeouts; implement circuit breaker pattern for resilience

## Resources

### API Development Frameworks
- Express.js and Fastify for Node.js APIs
- Flask and FastAPI for Python APIs
- Spring Boot for Java APIs
- Gin and Echo for Go APIs

### API Standards and Best Practices
- OpenAPI Specification 3.0+ for API documentation
- JSON:API specification for RESTful API conventions
- OAuth 2.0 and OpenID Connect for authentication
- HTTP/2 and HTTP/3 for performance optimization

### Testing and Monitoring Tools
- Postman and Insomnia for API testing
- Swagger UI for interactive API documentation
- Artillery and k6 for load testing
- Prometheus and Grafana for monitoring

### Security Best Practices
- OWASP API Security Top 10 guidelines
- JWT best practices for token-based auth
- Rate limiting strategies to prevent abuse
- Input validation and sanitization techniques

## Overview


This skill provides automated assistance for api throttling manager tasks.
This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.