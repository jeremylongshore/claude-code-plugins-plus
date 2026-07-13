# API Response Validation Examples

## Response Validation Middleware (Ajv)

```javascript
const Ajv = require('ajv');
const addFormats = require('ajv-formats');
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

function responseValidator(schemaMap) {
  return (req, res, next) => {
    const orig = res.json.bind(res);
    res.json = (body) => {
      const key = `${req.method}:${req.route?.path}:${res.statusCode}`;
      const schema = schemaMap[key];
      if (schema) {
        const validate = ajv.compile(schema);
        if (!validate(body)) {
          const isStrict = process.env.NODE_ENV !== 'production';
          logger.warn({ path: key, errors: validate.errors }, 'Response validation failed');
          responseValidationFailures.inc({ path: req.route?.path, status: res.statusCode });
          if (isStrict) {
            return orig({ title: 'Response Validation Error', errors: validate.errors });
          }
        }
      }
      return orig(body);
    };
    next();
  };
}
```

## Schema Map from OpenAPI

```javascript
// validators/compile-schemas.js
const yaml = require('js-yaml');
const fs = require('fs');

function compileSchemas(specPath) {
  const spec = yaml.load(fs.readFileSync(specPath));
  const schemaMap = {};

  for (const [path, methods] of Object.entries(spec.paths)) {
    for (const [method, operation] of Object.entries(methods)) {
      for (const [statusCode, response] of Object.entries(operation.responses || {})) {
        const schema = response?.content?.['application/json']?.schema;
        if (schema) {
          const key = `${method.toUpperCase()}:${path}:${statusCode}`;
          schemaMap[key] = resolveRefs(schema, spec.components?.schemas || {});
        }
      }
    }
  }
  return schemaMap;
}

const schemas = compileSchemas('./openapi.yaml');
app.use(responseValidator(schemas));
```

## User Response Schema

```json
{
  "type": "object",
  "required": ["id", "name", "email", "status", "createdAt"],
  "additionalProperties": false,
  "properties": {
    "id": { "type": "string", "pattern": "^usr_[a-zA-Z0-9]+$" },
    "name": { "type": "string", "minLength": 1 },
    "email": { "type": "string", "format": "email" },
    "status": { "type": "string", "enum": ["active", "inactive", "suspended"] },
    "createdAt": { "type": "string", "format": "date-time" }
  }
}
```

## Contract Test Suite

```javascript
describe('Response Contract Tests', () => {
  it('GET /users returns valid paginated list', async () => {
    const res = await request(app).get('/users?page=1&limit=5');
    expect(res.status).toBe(200);

    const { data, pagination } = res.body;
    expect(Array.isArray(data)).toBe(true);
    for (const user of data) {
      expect(user.id).toMatch(/^usr_/);
      expect(typeof user.name).toBe('string');
      expect(user.email).toMatch(/@/);
      expect(['active', 'inactive', 'suspended']).toContain(user.status);
      expect(new Date(user.createdAt).toISOString()).toBe(user.createdAt);
    }
    expect(pagination).toMatchObject({ page: 1, limit: 5 });
    expect(typeof pagination.total).toBe('number');
  });

  it('GET /users/:id returns valid user', async () => {
    const res = await request(app).get('/users/usr_test1');
    expect(res.status).toBe(200);
    expect(res.body).not.toHaveProperty('passwordHash');
    expect(res.body).toHaveProperty('id');
    expect(res.body).toHaveProperty('email');
  });

  it('POST /users returns 400 with field errors', async () => {
    const res = await request(app).post('/users')
      .send({ name: '', email: 'invalid' });
    expect(res.status).toBe(400);
    expect(res.body.errors).toBeDefined();
    expect(res.body.errors.length).toBeGreaterThan(0);
    for (const err of res.body.errors) {
      expect(err).toHaveProperty('field');
      expect(err).toHaveProperty('message');
    }
  });

  it('GET /users/nonexistent returns 404 RFC 7807', async () => {
    const res = await request(app).get('/users/nonexistent');
    expect(res.status).toBe(404);
    expect(res.body).toHaveProperty('type');
    expect(res.body).toHaveProperty('title');
    expect(res.body).toHaveProperty('status', 404);
  });
});
```

## Schema Drift Detection

```javascript
async function detectSchemaDrift(endpoint, schema) {
  const res = await fetch(`http://localhost:3000${endpoint}`);
  const body = await res.json();
  const actual = inferSchema(body);
  const diff = compareSchemas(schema, actual);

  if (diff.addedFields.length > 0) {
    logger.warn({ endpoint, fields: diff.addedFields }, 'Undocumented fields in response');
  }
  if (diff.removedFields.length > 0) {
    logger.error({ endpoint, fields: diff.removedFields }, 'Missing documented fields');
  }
  return diff;
}
```

## Backward Compatibility Check

```javascript
function checkBackwardCompatibility(v1Schema, v2Schema) {
  const issues = [];

  for (const field of v1Schema.required || []) {
    if (!v2Schema.properties?.[field]) {
      issues.push({ type: 'REMOVED_FIELD', field, severity: 'breaking' });
    }
  }

  for (const [field, v1Type] of Object.entries(v1Schema.properties || {})) {
    const v2Type = v2Schema.properties?.[field];
    if (v2Type && v1Type.type !== v2Type.type) {
      issues.push({ type: 'TYPE_CHANGED', field, from: v1Type.type, to: v2Type.type, severity: 'breaking' });
    }
  }

  return { compatible: issues.filter(i => i.severity === 'breaking').length === 0, issues };
}
```

## Production Sampling

```javascript
function sampledValidator(schemaMap, sampleRate = 0.05) {
  return (req, res, next) => {
    if (Math.random() > sampleRate) return next();
    return responseValidator(schemaMap)(req, res, next);
  };
}
app.use(sampledValidator(schemas, 0.05)); // Validate 5% of responses
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
