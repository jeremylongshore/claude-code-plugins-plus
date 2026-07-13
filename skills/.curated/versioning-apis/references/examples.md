# API Versioning Examples

## URL Path Versioning (Express)

```javascript
// routes/v1/users.js
const v1Router = express.Router();
v1Router.get('/users', async (req, res) => {
  const users = await db.users.findAll();
  // v1: returns flat array with 'name' field
  res.json(users.map(u => ({ id: u.id, name: `${u.firstName} ${u.lastName}`, email: u.email })));
});

// routes/v2/users.js
const v2Router = express.Router();
v2Router.get('/users', async (req, res) => {
  const users = await db.users.findAll();
  // v2: returns paginated with firstName/lastName
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 20;
  res.json({
    data: users.slice((page - 1) * limit, page * limit),
    pagination: { page, limit, total: users.length },
  });
});

// Mount versioned routes
app.use('/api/v1', v1Router);
app.use('/api/v2', v2Router);
```

## Header-Based Version Router

```javascript
// middleware/version-router.js
function versionRouter(handlers) {
  return (req, res, next) => {
    const accept = req.headers['accept'] || '';
    const versionMatch = accept.match(/application\/vnd\.myapi\.v(\d+)\+json/);
    const queryVersion = req.query.version;
    const version = versionMatch ? `v${versionMatch[1]}` : queryVersion || 'v2'; // default v2

    const handler = handlers[version];
    if (!handler) {
      return res.status(400).json({
        title: 'Unsupported Version',
        detail: `Version '${version}' not available. Supported: ${Object.keys(handlers).join(', ')}`,
      });
    }
    return handler(req, res, next);
  };
}

// Usage
app.get('/users', versionRouter({
  v1: v1ListUsers,
  v2: v2ListUsers,
}));
```

## Compatibility Layer (v1 on v2 Logic)

```javascript
// compatibility/v1-adapter.js
function v1CompatLayer(v2Handler) {
  return async (req, res) => {
    // Transform v1 request to v2 format
    if (req.body?.name) {
      const parts = req.body.name.split(' ');
      req.body.firstName = parts[0];
      req.body.lastName = parts.slice(1).join(' ');
      delete req.body.name;
    }

    // Call v2 handler
    const v2Response = await v2Handler(req);

    // Transform v2 response to v1 format
    if (Array.isArray(v2Response.data)) {
      return res.json(v2Response.data.map(u => ({
        ...u, name: `${u.firstName} ${u.lastName}`.trim(),
      })));
    }

    if (v2Response.firstName) {
      return res.json({
        ...v2Response,
        name: `${v2Response.firstName} ${v2Response.lastName}`.trim(),
      });
    }

    return res.json(v2Response);
  };
}
```

## Deprecation Headers

```javascript
// middleware/deprecation.js
const SUNSET_DATES = {
  v1: new Date('2026-09-01T00:00:00Z'),
};

function deprecationHeaders(version) {
  return (req, res, next) => {
    const sunsetDate = SUNSET_DATES[version];
    if (sunsetDate) {
      res.set('Deprecation', 'true');
      res.set('Sunset', sunsetDate.toUTCString());
      res.set('Link', '</docs/migration-v1-to-v2>; rel="sunset"');
    }
    next();
  };
}

function sunsetGate(version) {
  return (req, res, next) => {
    const sunsetDate = SUNSET_DATES[version];
    if (sunsetDate && new Date() > sunsetDate) {
      return res.status(410).json({
        title: 'Gone',
        detail: `API ${version} was sunset on ${sunsetDate.toISOString()}. Migrate to v2.`,
        migrationGuide: '/docs/migration-v1-to-v2',
      });
    }
    next();
  };
}

app.use('/api/v1', sunsetGate('v1'), deprecationHeaders('v1'), v1Router);
```

## Breaking Change Detector

```javascript
// utils/breaking-change-detector.js
function detectBreakingChanges(v1Spec, v2Spec) {
  const changes = [];

  for (const [path, v1Methods] of Object.entries(v1Spec.paths)) {
    const v2Methods = v2Spec.paths[path];
    if (!v2Methods) {
      changes.push({ type: 'REMOVED_ENDPOINT', path, breaking: true });
      continue;
    }

    for (const [method, v1Op] of Object.entries(v1Methods)) {
      const v2Op = v2Methods[method];
      if (!v2Op) {
        changes.push({ type: 'REMOVED_METHOD', path, method, breaking: true });
        continue;
      }

      // Check response schema changes
      const v1Schema = v1Op.responses?.['200']?.content?.['application/json']?.schema;
      const v2Schema = v2Op.responses?.['200']?.content?.['application/json']?.schema;
      if (v1Schema && v2Schema) {
        for (const field of v1Schema.required || []) {
          if (!v2Schema.properties?.[field]) {
            changes.push({ type: 'REMOVED_FIELD', path, field, breaking: true });
          }
        }
      }
    }
  }

  return { breaking: changes.filter(c => c.breaking), nonBreaking: changes.filter(c => !c.breaking) };
}
```

## Version Compatibility Tests

```javascript
describe('v1 backward compatibility', () => {
  it('GET /api/v1/users returns flat array with name field', async () => {
    const res = await request(app).get('/api/v1/users');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
    expect(res.body[0]).toHaveProperty('name');
    expect(res.body[0]).not.toHaveProperty('firstName');
  });

  it('GET /api/v2/users returns paginated with firstName', async () => {
    const res = await request(app).get('/api/v2/users');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('data');
    expect(res.body).toHaveProperty('pagination');
    expect(res.body.data[0]).toHaveProperty('firstName');
  });

  it('v1 includes Deprecation and Sunset headers', async () => {
    const res = await request(app).get('/api/v1/users');
    expect(res.headers['deprecation']).toBe('true');
    expect(res.headers['sunset']).toBeDefined();
  });
});
```

## curl: Version Behavior

```bash
# URL path versioning
curl http://localhost:3000/api/v1/users
# [{"id":"usr_1","name":"Alice Smith","email":"alice@example.com"}]

curl http://localhost:3000/api/v2/users
# {"data":[{"id":"usr_1","firstName":"Alice","lastName":"Smith"}],"pagination":{...}}

# Header-based versioning
curl http://localhost:3000/users -H "Accept: application/vnd.myapi.v1+json"
# Deprecation: true
# Sunset: Mon, 01 Sep 2026 00:00:00 GMT

# Sunset version returns 410
curl http://localhost:3000/api/v0/users
# 410 {"title":"Gone","detail":"API v0 was sunset...","migrationGuide":"/docs/migration"}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
