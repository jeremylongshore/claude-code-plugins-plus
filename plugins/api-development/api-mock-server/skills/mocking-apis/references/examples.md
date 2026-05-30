# API Mock Server Examples

## Prism Mock from OpenAPI

```bash
npx @stoplight/prism-cli mock openapi.yaml --port 4010

curl http://localhost:4010/users
# Returns schema-compliant random data

curl -X POST http://localhost:4010/users \
  -H "Content-Type: application/json" -d '{"name":"Alice","email":"alice@example.com"}'
# 201 with generated response

# Force specific status
curl http://localhost:4010/users/999 -H "Prefer: code=404"
```

## Stateful CRUD Mock Server

```javascript
const express = require('express');
const { faker } = require('@faker-js/faker');
const app = express();
app.use(express.json());

const state = {
  users: Array.from({ length: 10 }, () => ({
    id: `usr_${faker.string.alphanumeric(8)}`,
    name: faker.person.fullName(),
    email: faker.internet.email(),
    status: 'active',
    createdAt: faker.date.recent().toISOString(),
  })),
};

app.get('/users', (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 20;
  const start = (page - 1) * limit;
  res.json({
    data: state.users.slice(start, start + limit),
    pagination: { page, limit, total: state.users.length },
  });
});

app.get('/users/:id', (req, res) => {
  const user = state.users.find(u => u.id === req.params.id);
  if (!user) return res.status(404).json({ detail: 'User not found' });
  res.json(user);
});

app.post('/users', (req, res) => {
  const user = {
    id: `usr_${faker.string.alphanumeric(8)}`, ...req.body,
    status: 'active', createdAt: new Date().toISOString(),
  };
  state.users.push(user);
  res.status(201).json(user);
});

app.put('/users/:id', (req, res) => {
  const i = state.users.findIndex(u => u.id === req.params.id);
  if (i === -1) return res.status(404).json({ detail: 'Not found' });
  state.users[i] = { ...state.users[i], ...req.body };
  res.json(state.users[i]);
});

app.delete('/users/:id', (req, res) => {
  const i = state.users.findIndex(u => u.id === req.params.id);
  if (i === -1) return res.status(404).json({ detail: 'Not found' });
  state.users.splice(i, 1);
  res.status(204).end();
});

app.post('/mock/reset', (req, res) => { state.users = []; res.json({ message: 'State reset' }); });
app.listen(4010, () => console.log('Mock server on :4010'));
```

## MSW for Node.js Tests

```javascript
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const handlers = [
  http.get('/api/users', () => HttpResponse.json({
    data: [{ id: 'usr_001', name: 'Alice', email: 'alice@example.com' }],
    pagination: { page: 1, limit: 20, total: 1 },
  })),
  http.get('/api/users/:id', ({ params }) => {
    if (params.id === 'notfound') return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    return HttpResponse.json({ id: params.id, name: 'Alice', email: 'alice@example.com' });
  }),
  http.post('/api/users', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: 'usr_new', ...body }, { status: 201 });
  }),
];

const server = setupServer(...handlers);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('lists users', async () => {
  const res = await fetch('/api/users');
  const data = await res.json();
  expect(data.data).toHaveLength(1);
});

test('handles 404', async () => {
  const res = await fetch('/api/users/notfound');
  expect(res.status).toBe(404);
});
```

## Error Scenario Middleware

```javascript
const errorScenarios = {
  'rate-limit': (req, res, next) => {
    if (Math.random() < 0.3) return res.status(429).json({ detail: 'Rate limited', retryAfter: 30 });
    next();
  },
  'server-errors': (req, res, next) => {
    if (Math.random() < 0.1) return res.status(500).json({ detail: 'Internal error' });
    next();
  },
  'latency': (req, res, next) => setTimeout(next, Math.floor(Math.random() * 500) + 50),
};

app.use((req, res, next) => {
  const scenario = req.query.scenario;
  if (scenario && errorScenarios[scenario]) return errorScenariosscenario;
  next();
});
```

## Request Recording

```javascript
const recordings = [];
app.use((req, res, next) => {
  const record = { timestamp: new Date().toISOString(), method: req.method, path: req.path, body: req.body };
  const orig = res.json.bind(res);
  res.json = (body) => { record.response = { status: res.statusCode, body }; recordings.push(record); return orig(body); };
  next();
});
app.get('/mock/recordings', (req, res) => res.json(recordings));
app.delete('/mock/recordings', (req, res) => { recordings.length = 0; res.json({ cleared: true }); });
```

## Docker Compose

```yaml
version: '3.8'
services:
  mock-api:
    build: ./mocks
    ports: ["4010:4010"]
    volumes: ["./mocks/fixtures:/app/fixtures"]
    environment: { PORT: "4010", LATENCY_MIN: "20", LATENCY_MAX: "200" }
```

## curl: Mock Server Usage

```bash
curl http://localhost:4010/users
# {"data":[...],"pagination":{"page":1,"limit":20,"total":10}}

curl -X POST http://localhost:4010/users \
  -H "Content-Type: application/json" -d '{"name":"New User","email":"new@example.com"}'
# {"id":"usr_xyz","name":"New User","status":"active"}

curl "http://localhost:4010/users?scenario=rate-limit"
# 429 {"detail":"Rate limited","retryAfter":30}

curl -X POST http://localhost:4010/mock/reset
# {"message":"State reset"}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
