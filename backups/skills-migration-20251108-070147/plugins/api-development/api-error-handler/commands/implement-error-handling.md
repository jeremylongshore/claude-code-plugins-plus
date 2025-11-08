---
description: Implement standardized API error handling
shortcut: errors
---

# Implement Error Handling

Create standardized, production-ready error handling middleware with proper HTTP status codes, consistent error formats, and comprehensive logging. This command generates custom error classes, middleware, and error recovery strategies for Node.js, Python, and other backend frameworks.

## Design Decisions

**Why standardized error handling matters:**
- **Client experience**: Consistent error formats make client integration predictable
- **Debugging**: Structured errors with context accelerate troubleshooting
- **Security**: Proper error handling prevents information leakage in production
- **Monitoring**: Standardized errors integrate cleanly with observability tools

**Alternatives considered:**
- **HTTP-only errors**: Simpler but lacks context for debugging
- **Framework defaults**: Inconsistent across endpoints, lacks business context
- **Exception-based only**: Can leak sensitive information, harder to test

**This approach balances**: Developer experience, security, debugging, and API consistency.

## When to Use

Use this command when:
- Starting a new API project that needs error handling
- Refactoring inconsistent error responses across endpoints
- Adding error monitoring and alerting to an existing API
- Migrating from generic framework errors to business-specific errors
- Implementing error handling for microservices that need consistency

Don't use when:
- Your framework's default error handling already meets your needs
- Building proof-of-concept code without production requirements
- Working with legacy systems that can't adopt new error formats

## Prerequisites

- Node.js 16+ (for Express/Fastify examples) or Python 3.8+ (for Flask/FastAPI)
- Existing API project structure
- Basic understanding of HTTP status codes (4xx client errors, 5xx server errors)
- (Optional) Logging framework installed (Winston, Pino, Structlog)
- (Optional) Monitoring service (Sentry, DataDog, New Relic)

## Process

1. **Generate Custom Error Classes**
   - Create base error class with HTTP status codes
   - Define specific error types (ValidationError, NotFoundError, AuthError)
   - Add error codes for programmatic handling

2. **Build Error Middleware**
   - Catch all errors in centralized handler
   - Format errors consistently (RFC 7807 Problem Details or custom)
   - Handle both operational and programmer errors

3. **Configure Environment-Specific Behavior**
   - Development: Include stack traces, detailed messages
   - Production: Sanitize errors, log internally, return safe messages

4. **Integrate Logging**
   - Log all errors with context (request ID, user, endpoint)
   - Add severity levels (error, warning, critical)
   - Include metadata for troubleshooting

5. **Add Error Recovery**
   - Graceful degradation strategies
   - Retry logic for transient failures
   - Circuit breaker integration

## Output Format

### Express.js Error Handler

```javascript
// errors/AppError.js
class AppError extends Error {
  constructor(message, statusCode, errorCode = null) {
    super(message);
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.isOperational = true;
    this.timestamp = new Date().toISOString();
    Error.captureStackTrace(this, this.constructor);
  }
}

class ValidationError extends AppError {
  constructor(message, errors = []) {
    super(message, 400, 'VALIDATION_ERROR');
    this.errors = errors;
  }
}

class NotFoundError extends AppError {
  constructor(resource) {
    super(`${resource} not found`, 404, 'NOT_FOUND');
    this.resource = resource;
  }
}

class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized') {
    super(message, 401, 'UNAUTHORIZED');
  }
}

class ForbiddenError extends AppError {
  constructor(message = 'Forbidden') {
    super(message, 403, 'FORBIDDEN');
  }
}

module.exports = { AppError, ValidationError, NotFoundError, UnauthorizedError, ForbiddenError };

// middleware/errorHandler.js
const logger = require('../utils/logger');

const errorHandler = (err, req, res, next) => {
  // Default to 500 server error
  let statusCode = err.statusCode || 500;
  let message = err.message || 'Internal Server Error';

  // Log error with context
  logger.error({
    message: err.message,
    statusCode,
    errorCode: err.errorCode,
    stack: err.stack,
    path: req.path,
    method: req.method,
    requestId: req.id,
    userId: req.user?.id,
    ip: req.ip
  });

  // Production: Don't leak error details
  if (process.env.NODE_ENV === 'production' && !err.isOperational) {
    message = 'An unexpected error occurred';
    statusCode = 500;
  }

  // Send error response
  res.status(statusCode).json({
    error: {
      message,
      code: err.errorCode,
      statusCode,
      timestamp: err.timestamp || new Date().toISOString(),
      path: req.path,
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
      ...(err.errors && { details: err.errors })
    }
  });
};

module.exports = errorHandler;
```

### FastAPI (Python) Error Handler

```python
# errors/exceptions.py
from typing import Optional, Any, Dict
from fastapi import HTTPException
from datetime import datetime

class AppError(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(status_code=status_code, detail=message)

class ValidationError(AppError):
    def __init__(self, message: str, errors: list = None):
        super().__init__(
            status_code=400,
            message=message,
            error_code="VALIDATION_ERROR",
            details={"errors": errors or []}
        )

class NotFoundError(AppError):
    def __init__(self, resource: str):
        super().__init__(
            status_code=404,
            message=f"{resource} not found",
            error_code="NOT_FOUND",
            details={"resource": resource}
        )

class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            status_code=401,
            message=message,
            error_code="UNAUTHORIZED"
        )

# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.error(
        f"AppError: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.error_code,
                "statusCode": exc.status_code,
                "timestamp": exc.timestamp,
                "path": str(request.url.path),
                **exc.details
            }
        }
    )

@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", exc_info=exc)

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "code": "INTERNAL_ERROR",
                "statusCode": 500,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

## Example Usage

### Example 1: Handling Validation Errors

```javascript
const { ValidationError } = require('./errors/AppError');
const { body, validationResult } = require('express-validator');

router.post('/users',
  [
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 8 }),
    body('name').trim().notEmpty()
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        throw new ValidationError('Validation failed', errors.array());
      }

      const user = await createUser(req.body);
      res.status(201).json(user);
    } catch (error) {
      next(error);
    }
  }
);

// Response for invalid input:
// {
//   "error": {
//     "message": "Validation failed",
//     "code": "VALIDATION_ERROR",
//     "statusCode": 400,
//     "timestamp": "2025-10-11T12:00:00.000Z",
//     "path": "/users",
//     "details": [
//       { "field": "email", "message": "Invalid email format" },
//       { "field": "password", "message": "Password must be at least 8 characters" }
//     ]
//   }
// }
```

### Example 2: Resource Not Found

```python
from fastapi import APIRouter
from errors.exceptions import NotFoundError

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await db.get_user(user_id)
    if not user:
        raise NotFoundError("User")
    return user

# Response:
# {
#   "error": {
#     "message": "User not found",
#     "code": "NOT_FOUND",
#     "statusCode": 404,
#     "timestamp": "2025-10-11T12:00:00.000Z",
#     "path": "/users/123",
#     "details": {
#       "resource": "User"
#     }
#   }
# }
```

### Example 3: Error with Retry Strategy

```javascript
const { AppError } = require('./errors/AppError');
const retry = require('async-retry');

async function callExternalAPI(endpoint) {
  return retry(async (bail, attempt) => {
    try {
      const response = await fetch(endpoint);
      if (!response.ok) {
        // Don't retry client errors
        if (response.status >= 400 && response.status < 500) {
          bail(new AppError('External API error', response.status));
          return;
        }
        // Retry server errors
        throw new Error(`API returned ${response.status}`);
      }
      return response.json();
    } catch (error) {
      console.log(`Attempt ${attempt} failed: ${error.message}`);
      throw error;
    }
  }, {
    retries: 3,
    minTimeout: 1000,
    maxTimeout: 5000
  });
}
```

## Error Handling

**Common issues and solutions:**

**Problem**: Errors logged multiple times
- **Cause**: Error handlers at multiple middleware layers
- **Solution**: Log only in the central error handler, not in route handlers

**Problem**: Stack traces visible in production
- **Cause**: Environment check not working correctly
- **Solution**: Verify `NODE_ENV=production` is set, check conditional logic

**Problem**: Lost error context (request ID, user info)
- **Cause**: Context not attached to request object
- **Solution**: Use middleware to attach request ID, user before error handler

**Problem**: Async errors not caught
- **Cause**: Missing try-catch or next() in async routes
- **Solution**: Use express-async-errors or wrap all async routes

**Problem**: Database connection errors crashing app
- **Cause**: Uncaught promise rejections
- **Solution**: Add process-level error handlers:

```javascript
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection', { reason, promise });
  // Optionally exit: process.exit(1);
});

process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception', { error });
  process.exit(1); // Must exit, app is in undefined state
});
```

## Configuration

### Error Handler Options

```javascript
const errorHandlerOptions = {
  // Include stack traces
  showStack: process.env.NODE_ENV === 'development',

  // Log level for different error types
  logLevel: {
    operational: 'error',
    programmer: 'critical'
  },

  // Send errors to monitoring service
  reportToMonitoring: process.env.NODE_ENV === 'production',

  // Sanitize sensitive fields
  sanitizeFields: ['password', 'ssn', 'creditCard'],

  // Custom error formatters
  formatters: {
    json: (err) => ({ error: err.toJSON() }),
    xml: (err) => convertToXML(err)
  }
};
```

## Best Practices

DO:
- Log all errors with sufficient context for debugging
- Use specific error classes for different failure scenarios
- Return consistent error format across all endpoints
- Sanitize errors in production (no stack traces, no sensitive data)
- Include correlation IDs for tracing errors across services
- Test error handling as thoroughly as success cases
- Document error codes and responses in API documentation

DON'T:
- Expose internal implementation details in error messages
- Log sensitive data (passwords, tokens, PII)
- Ignore errors or swallow exceptions silently
- Use generic "Error occurred" messages without context
- Return different error formats from different endpoints
- Forget to handle async errors (use try-catch or error middleware)
- Let programmer errors (bugs) be handled the same as operational errors

TIPS:
- Use error codes clients can handle programmatically (`INSUFFICIENT_FUNDS`, `RATE_LIMIT_EXCEEDED`)
- Provide actionable error messages ("Email already registered, try logging in" not "Duplicate entry")
- Group related errors with similar status codes (all validation = 400, all auth = 401/403)
- Consider RFC 7807 Problem Details format for standardization
- Add request IDs to errors for log correlation
- Monitor error rates and alert on anomalies

## Related Commands

- `/validate-api-responses` - Validate API responses match schemas
- `/setup-logging` - Configure structured logging for errors
- `/scan-api-security` - Scan for security vulnerabilities in error handling
- `/create-monitoring` - Set up error monitoring dashboards
- `/generate-rest-api` - Generate REST API with built-in error handling

## Performance Considerations

- **Error creation overhead**: Custom error classes add minimal overhead (~1-2ms)
- **Stack trace capture**: Can be expensive in hot paths, consider disabling in production
- **Logging**: Use async logging to avoid blocking request threads
- **Monitoring**: Batch error reports to external services (Sentry, DataDog)
- **Memory leaks**: Ensure errors don't hold references to large objects

**Optimization strategies:**
```javascript
// Disable stack traces in production for performance
if (process.env.NODE_ENV === 'production') {
  Error.stackTraceLimit = 0;
}

// Use structured logging with async writes
const logger = winston.createLogger({
  transports: [
    new winston.transports.File({
      filename: 'error.log',
      level: 'error'
    })
  ]
});
```

## Security Considerations

- **Information disclosure**: Never expose database errors, file paths, or internal IDs
- **Error-based enumeration**: Avoid revealing if resources exist ("Invalid credentials" not "User not found")
- **DoS via errors**: Rate limit error-triggering requests
- **Log injection**: Sanitize user input before logging
- **Sensitive data in logs**: Redact passwords, tokens, SSNs before logging

**Security checklist:**
```javascript
// BAD: Exposes internal structure
throw new Error(`User ${userId} not found in users table`);

// GOOD: Generic message
throw new NotFoundError('User');

// BAD: Reveals existence
if (!user) throw new Error('User not found');
if (password !== user.password) throw new Error('Wrong password');

// GOOD: Generic auth failure
if (!user || password !== user.password) {
  throw new UnauthorizedError('Invalid credentials');
}
```

## Troubleshooting

**Error handler not catching errors:**
1. Ensure error handler is registered AFTER all routes
2. Check async routes call `next(error)` or use express-async-errors
3. Verify middleware order: routes → 404 handler → error handler

**Errors not logged:**
1. Check logger configuration and file permissions
2. Verify log level settings (error should be logged at all levels)
3. Test logger independently before integration

**Production errors too verbose:**
1. Verify NODE_ENV=production environment variable
2. Check conditional stack trace logic
3. Test with actual production config locally

**Error monitoring not working:**
1. Verify API keys for Sentry/DataDog/New Relic
2. Check network connectivity to monitoring service
3. Test error reporting independently

## Version History

- **1.0.0** (2025-10-11): Initial release with Express and FastAPI examples
  - Custom error classes (ValidationError, NotFoundError, AuthError)
  - Environment-specific error formatting
  - Structured logging integration
  - Error recovery patterns
