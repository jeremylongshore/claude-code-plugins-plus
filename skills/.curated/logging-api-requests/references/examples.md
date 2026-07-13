# API Request Logger Examples

## Structured Logging Middleware (Pino)

```javascript
const pino = require('pino');
const logger = pino({ level: process.env.LOG_LEVEL || 'info' });

function requestLogger(req, res, next) {
  const start = process.hrtime.bigint();
  const correlationId = req.headers['x-request-id'] || crypto.randomUUID();
  req.correlationId = correlationId;
  req.log = logger.child({ correlationId });
  res.set('X-Request-ID', correlationId);

  res.on('finish', () => {
    const durationMs = Number(process.hrtime.bigint() - start) / 1e6;
    const data = {
      correlationId, method: req.method,
      path: req.originalUrl.split('?')[0],
      status: res.statusCode, durationMs: Math.round(durationMs),
      userId: req.user?.id || null,
    };
    if (res.statusCode >= 500) logger.error(data, 'Server error');
    else if (res.statusCode >= 400) logger.warn(data, 'Client error');
    else logger.info(data, 'Request completed');
  });
  next();
}
```

## JSON Log Output

```json
{
  "level": "info",
  "timestamp": "2026-03-10T14:30:00.123Z",
  "correlationId": "req_a1b2c3d4",
  "method": "POST",
  "path": "/api/users",
  "status": 201,
  "durationMs": 45,
  "userId": "usr_456",
  "msg": "Request completed"
}
```

## Correlation ID Propagation

```javascript
function correlationId(req, res, next) {
  const id = req.headers['x-request-id'] || crypto.randomUUID();
  req.correlationId = id;
  res.set('X-Request-ID', id);
  next();
}

async function callDownstream(url, req) {
  return fetch(url, { headers: { 'X-Request-ID': req.correlationId } });
}
```

## PII Redaction

```javascript
const REDACT_PATTERNS = [
  { field: 'password', replacement: '[REDACTED]' },
  { field: 'token', replacement: '[REDACTED]' },
  { field: 'authorization', replacement: 'Bearer [REDACTED]' },
  { field: 'ssn', replacement: '***-**-****' },
  { field: 'email', replacement: (v) => v.replace(/^(.{2}).*@/, '$1***@') },
];

function redactPII(obj, depth = 0) {
  if (depth > 10 || !obj || typeof obj !== 'object') return obj;
  const result = Array.isArray(obj) ? [...obj] : { ...obj };
  for (const key of Object.keys(result)) {
    const pattern = REDACT_PATTERNS.find(p => key.toLowerCase().includes(p.field));
    if (pattern) {
      result[key] = typeof pattern.replacement === 'function'
        ? pattern.replacement(result[key]) : pattern.replacement;
    } else if (typeof result[key] === 'object') {
      result[key] = redactPII(result[key], depth + 1);
    }
  }
  return result;
}
// { email: "alice@example.com", password: "secret" }
// -> { email: "al***@example.com", password: "[REDACTED]" }
```

## Audit Logger

```javascript
const auditLogger = pino({ transport: { target: 'pino/file', options: { destination: './logs/audit.log' } } });

function auditLog(req, action, resource, details = {}) {
  auditLogger.info({
    audit: true, correlationId: req.correlationId,
    userId: req.user?.id, ip: req.ip, action, resource, ...details,
  });
}

app.post('/api/users', async (req, res) => {
  const user = await createUser(req.body);
  auditLog(req, 'CREATE', 'user', { targetId: user.id });
  res.status(201).json(user);
});

app.delete('/api/users/:id', async (req, res) => {
  await deleteUser(req.params.id);
  auditLog(req, 'DELETE', 'user', { targetId: req.params.id });
  res.status(204).end();
});
```

## Error Body Logging

```javascript
function logErrorBodies(req, res, next) {
  const orig = res.json.bind(res);
  res.json = (body) => {
    if (res.statusCode >= 400) {
      req.log.warn({ responseStatus: res.statusCode, responseBody: redactPII(body) }, 'Error response');
    }
    return orig(body);
  };
  next();
}
```

## Log Querying Examples

```bash
# Find all logs for a correlation ID
cat logs/app.log | jq 'select(.correlationId == "req_abc123")'

# Find slow requests
cat logs/app.log | jq 'select(.durationMs > 1000)'

# Audit trail for a user
cat logs/audit.log | jq 'select(.userId == "usr_456")'

# All failed logins from an IP
cat logs/audit.log | jq 'select(.action == "LOGIN_FAILURE" and .ip == "192.168.1.100")'
```

## PII Redaction Tests

```javascript
describe('PII Redactor', () => {
  it('redacts passwords', () => {
    expect(redactPII({ password: 'secret' }).password).toBe('[REDACTED]');
  });
  it('redacts nested emails', () => {
    const out = redactPII({ user: { email: 'alice@example.com', name: 'Alice' } });
    expect(out.user.email).toBe('al***@example.com');
    expect(out.user.name).toBe('Alice');
  });
  it('handles auth headers', () => {
    expect(redactPII({ authorization: 'Bearer eyJ...' }).authorization).toBe('Bearer [REDACTED]');
  });
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
