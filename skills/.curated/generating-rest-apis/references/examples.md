# REST API Generator Examples

## Express CRUD Endpoints

```javascript
// routes/users.js
const express = require('express');
const router = express.Router();

// GET /users - List with pagination, filtering, sorting
router.get('/', async (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = Math.min(parseInt(req.query.limit) || 20, 100);
  const offset = (page - 1) * limit;
  const sort = req.query.sort || '-createdAt'; // '-' prefix = descending

  const where = {};
  if (req.query.status) where.status = req.query.status;
  if (req.query.search) where.name = { $iLike: `%${req.query.search}%` };

  const [data, total] = await Promise.all([
    db.users.findAll({ where, limit, offset, order: parseSortParam(sort) }),
    db.users.count({ where }),
  ]);

  res.json({ data, pagination: { page, limit, total, pages: Math.ceil(total / limit) } });
});

// GET /users/:id
router.get('/:id', async (req, res) => {
  const user = await db.users.findById(req.params.id);
  if (!user) throw new NotFoundError('User', req.params.id);

  const fields = req.query.fields?.split(',');
  res.json(fields ? pick(user, fields) : user);
});

// POST /users
router.post('/', authenticateToken, async (req, res) => {
  const data = CreateUserSchema.parse(req.body);
  const user = await db.users.create(data);
  res.status(201).json(user);
});

// PUT /users/:id
router.put('/:id', authenticateToken, async (req, res) => {
  const data = UpdateUserSchema.parse(req.body);
  const user = await db.users.findById(req.params.id);
  if (!user) throw new NotFoundError('User', req.params.id);
  const updated = await db.users.update(req.params.id, data);
  res.json(updated);
});

// DELETE /users/:id
router.delete('/:id', authenticateToken, requireRole('admin'), async (req, res) => {
  const user = await db.users.findById(req.params.id);
  if (!user) throw new NotFoundError('User', req.params.id);
  await db.users.destroy(req.params.id);
  res.status(204).end();
});

app.use('/api/users', router);
```

## Request Validation (Zod)

```javascript
// middleware/validate.js
const { z } = require('zod');

const CreateUserSchema = z.object({
  name: z.string().min(1).max(255),
  email: z.string().email(),
  role: z.enum(['user', 'admin']).default('user'),
});

const UpdateUserSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  email: z.string().email().optional(),
  status: z.enum(['active', 'inactive', 'suspended']).optional(),
});

function validate(schema) {
  return (req, res, next) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      return res.status(400).json({
        type: 'https://api.example.com/errors/validation',
        title: 'Validation Error',
        status: 400,
        errors: result.error.issues.map(i => ({
          field: i.path.join('.'), message: i.message, code: i.code,
        })),
      });
    }
    req.body = result.data;
    next();
  };
}

router.post('/', authenticateToken, validate(CreateUserSchema), createUser);
```

## FastAPI Implementation (Python)

```python
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

app = FastAPI()

class CreateUser(BaseModel):
    name: str
    email: EmailStr
    role: str = "user"

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    status: str

@app.get("/users", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    sort: str = "-created_at",
):
    offset = (page - 1) * limit
    users = await db.users.find(status=status, limit=limit, offset=offset, sort=sort)
    total = await db.users.count(status=status)
    return {"data": users, "pagination": {"page": page, "limit": limit, "total": total}}

@app.post("/users", status_code=201, response_model=UserResponse)
async def create_user(user: CreateUser):
    return await db.users.create(user.dict())

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    user = await db.users.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return user

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: str):
    await db.users.delete(user_id)
```

## curl: CRUD Operations

```bash
# List with pagination and filtering
curl "http://localhost:3000/api/users?page=1&limit=10&status=active&sort=-createdAt"
# {"data":[...],"pagination":{"page":1,"limit":10,"total":42,"pages":5}}

# Get with field selection
curl "http://localhost:3000/api/users/usr_123?fields=id,name,email"
# {"id":"usr_123","name":"Alice","email":"alice@example.com"}

# Create
curl -X POST http://localhost:3000/api/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Smith","email":"alice@example.com","role":"user"}'
# 201 {"id":"usr_abc","name":"Alice Smith","email":"alice@example.com","status":"active"}

# Update
curl -X PUT http://localhost:3000/api/users/usr_abc \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Johnson"}'
# {"id":"usr_abc","name":"Alice Johnson",...}

# Delete
curl -X DELETE http://localhost:3000/api/users/usr_abc \
  -H "Authorization: Bearer $TOKEN"
# 204 No Content

# Validation error
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" -d '{"name":"","email":"bad"}'
# 400 {"errors":[{"field":"name","message":"Too short"},{"field":"email","message":"Invalid email"}]}
```

## Integration Tests

```javascript
describe('Users API', () => {
  it('lists users with pagination', async () => {
    const res = await request(app).get('/api/users?page=1&limit=5');
    expect(res.status).toBe(200);
    expect(res.body.data.length).toBeLessThanOrEqual(5);
    expect(res.body.pagination).toMatchObject({ page: 1, limit: 5 });
  });

  it('creates user', async () => {
    const res = await request(app).post('/api/users')
      .set('Authorization', `Bearer ${token}`)
      .send({ name: 'Test', email: 'test@example.com' });
    expect(res.status).toBe(201);
    expect(res.body.id).toMatch(/^usr_/);
  });

  it('returns 404 for missing user', async () => {
    const res = await request(app).get('/api/users/nonexistent');
    expect(res.status).toBe(404);
  });

  it('returns 401 without auth', async () => {
    const res = await request(app).post('/api/users').send({ name: 'X', email: 'x@y.com' });
    expect(res.status).toBe(401);
  });
});
```

## Sort Parameter Parser

```javascript
function parseSortParam(sort) {
  return sort.split(',').map(field => {
    if (field.startsWith('-')) return [field.slice(1), 'DESC'];
    return [field, 'ASC'];
  });
}
// "-createdAt,name" -> [['createdAt', 'DESC'], ['name', 'ASC']]
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
