# API Error Handling Examples

## RFC 7807 Problem Details Response

```json
{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 400,
  "detail": "Request body contains 2 validation errors",
  "instance": "/users",
  "errors": [
    { "field": "email", "message": "Invalid email format", "code": "INVALID_FORMAT" },
    { "field": "name", "message": "Must be at least 1 character", "code": "TOO_SHORT" }
  ]
}
```

## Typed Error Classes

```javascript
// errors/http-errors.js
class AppError extends Error {
  constructor(message, status, type, details = {}) {
    super(message);
    this.status = status;
    this.type = type;
    this.details = details;
  }
  toRFC7807(path) {
    return {
      type: `https://api.example.com/errors/${this.type}`,
      title: this.message, status: this.status,
      detail: this.details.detail || this.message,
      instance: path, ...this.details,
    };
  }
}

class ValidationError extends AppError {
  constructor(errors) { super('Validation Error', 400, 'validation', { errors }); }
}
class NotFoundError extends AppError {
  constructor(resource, id) {
    super('Not Found', 404, 'not-found', { detail: `${resource} '${id}' not found` });
  }
}
class ConflictError extends AppError {
  constructor(field, value) {
    super('Conflict', 409, 'conflict', { detail: `${field} '${value}' already exists` });
  }
}
class AuthenticationError extends AppError {
  constructor(detail = 'Invalid or missing authentication') {
    super('Authentication Required', 401, 'authentication', { detail });
  }
}
class RateLimitError extends AppError {
  constructor(retryAfter) {
    super('Too Many Requests', 429, 'rate-limit', { detail: 'Rate limit exceeded', retryAfter });
  }
}
```

## Centralized Error Handler Middleware

```javascript
// middleware/error-handler.js
function errorHandler(err, req, res, next) {
  const correlationId = req.headers['x-request-id'] || crypto.randomUUID();

  if (err instanceof AppError) {
    const body = err.toRFC7807(req.originalUrl);
    body.correlationId = correlationId;
    logger.warn({ err, correlationId, path: req.originalUrl });
    return res.status(err.status).json(body);
  }

  if (err.name === 'ZodError') {
    const errors = err.issues.map(i => ({
      field: i.path.join('.'), message: i.message, code: i.code,
    }));
    return res.status(400).json({
      type: 'https://api.example.com/errors/validation',
      title: 'Validation Error', status: 400,
      detail: `${errors.length} validation error(s)`,
      correlationId, errors,
    });
  }

  if (err.code === '23505') { // PostgreSQL unique violation
    return res.status(409).json({
      type: 'https://api.example.com/errors/conflict',
      title: 'Conflict', status: 409, correlationId,
    });
  }

  logger.error({ err, correlationId, stack: err.stack });
  Sentry.captureException(err, { extra: { correlationId } });

  const isProd = process.env.NODE_ENV === 'production';
  res.status(500).json({
    type: 'https://api.example.com/errors/internal',
    title: 'Internal Server Error', status: 500,
    detail: isProd ? 'An unexpected error occurred' : err.message,
    correlationId, ...(isProd ? {} : { stack: err.stack }),
  });
}

app.use(errorHandler);
```

## Usage in Route Handlers

```javascript
app.get('/users/:id', async (req, res) => {
  const user = await db.users.findById(req.params.id);
  if (!user) throw new NotFoundError('User', req.params.id);
  res.json(user);
});

app.post('/users', async (req, res) => {
  const parsed = CreateUserSchema.safeParse(req.body);
  if (!parsed.success) {
    throw new ValidationError(parsed.error.issues.map(i => ({
      field: i.path.join('.'), message: i.message, code: i.code,
    })));
  }
  const existing = await db.users.findByEmail(parsed.data.email);
  if (existing) throw new ConflictError('email', parsed.data.email);
  const user = await db.users.create(parsed.data);
  res.status(201).json(user);
});
```

## curl: Error Responses

```bash
# 404
curl -i http://localhost:3000/users/nonexistent
# {"type":"...not-found","title":"Not Found","status":404,
#  "detail":"User 'nonexistent' not found","correlationId":"req_abc123"}

# 400 validation
curl -X POST http://localhost:3000/users \
  -H "Content-Type: application/json" -d '{"name":"","email":"bad"}'
# {"type":"...validation","title":"Validation Error","status":400,
#  "errors":[{"field":"name","message":"Too short"},{"field":"email","message":"Invalid email"}]}

# 429 rate limit
curl -i http://localhost:3000/auth/login
# Retry-After: 45
# {"type":"...rate-limit","detail":"Rate limit exceeded","retryAfter":45}
```

## FastAPI Error Handling (Python)

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

class APIError(Exception):
    def __init__(self, status, error_type, title, detail):
        self.status = status
        self.error_type = error_type
        self.title = title
        self.detail = detail

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(status_code=exc.status, content={
        "type": f"https://api.example.com/errors/{exc.error_type}",
        "title": exc.title, "status": exc.status,
        "detail": exc.detail, "instance": str(request.url.path),
    })

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await db.users.find(user_id)
    if not user:
        raise APIError(404, "not-found", "Not Found", f"User '{user_id}' not found")
    return user
```

## Process-Level Safety Nets

```javascript
process.on('unhandledRejection', (reason) => {
  logger.error('Unhandled rejection', { reason });
  Sentry.captureException(reason);
});

process.on('uncaughtException', (error) => {
  logger.fatal('Uncaught exception', { error });
  Sentry.captureException(error);
  process.exit(1);
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
