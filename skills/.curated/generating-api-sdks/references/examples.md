# API SDK Generation Examples

## Generated TypeScript SDK Client

```typescript
// sdk/typescript/src/client.ts
export class APIClient {
  private baseUrl: string;
  private token: string;
  private maxRetries: number;

  constructor(config: { baseUrl: string; token: string; maxRetries?: number }) {
    this.baseUrl = config.baseUrl;
    this.token = config.token;
    this.maxRetries = config.maxRetries ?? 3;
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      const res = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
      });

      if (res.status === 429 || res.status >= 500) {
        if (attempt < this.maxRetries) {
          const delay = Math.pow(2, attempt) * 1000;
          await new Promise(r => setTimeout(r, delay));
          continue;
        }
      }

      if (!res.ok) {
        const error = await res.json();
        throw new APIError(res.status, error.detail || 'Request failed');
      }
      return res.json() as T;
    }
    throw new APIError(500, 'Max retries exceeded');
  }

  async listUsers(params?: { page?: number; limit?: number }): Promise<UserListResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.limit) query.set('limit', String(params.limit));
    return this.request('GET', `/users?${query}`);
  }

  async getUser(id: string): Promise<User> {
    return this.request('GET', `/users/${id}`);
  }

  async createUser(data: CreateUserRequest): Promise<User> {
    return this.request('POST', '/users', data);
  }

  async deleteUser(id: string): Promise<void> {
    await this.request('DELETE', `/users/${id}`);
  }

  async *listAllUsers(pageSize = 20): AsyncGenerator<User> {
    let page = 1;
    while (true) {
      const res = await this.listUsers({ page, limit: pageSize });
      for (const user of res.data) yield user;
      if (res.data.length < pageSize) break;
      page++;
    }
  }
}
```

## TypeScript Type Definitions

```typescript
// sdk/typescript/src/models/user.ts
export interface User {
  id: string;
  name: string;
  email: string;
  status: 'active' | 'inactive' | 'suspended';
  createdAt: string;
}

export interface CreateUserRequest {
  name: string;
  email: string;
  role?: 'user' | 'admin';
}

export interface UserListResponse {
  data: User[];
  pagination: { page: number; limit: number; total: number };
}

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}
```

## SDK Usage (TypeScript)

```typescript
const client = new APIClient({
  baseUrl: 'https://api.example.com',
  token: 'sk_live_abc123',
});

// List users
const users = await client.listUsers({ page: 1, limit: 20 });
console.log(users.pagination.total);

// Create user
const user = await client.createUser({ name: 'Alice', email: 'alice@example.com' });

// Paginate all users with async iterator
for await (const user of client.listAllUsers()) {
  console.log(user.name);
}
```

## Python SDK with Async Support

```python
# sdk/python/client.py
import httpx
from dataclasses import dataclass
from typing import AsyncIterator, Optional

@dataclass
class User:
    id: str
    name: str
    email: str
    status: str
    created_at: str

class APIClient:
    def __init__(self, base_url: str, token: str, max_retries: int = 3):
        self.base_url = base_url
        self.token = token
        self.max_retries = max_retries

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def list_users(self, page: int = 1, limit: int = 20) -> dict:
        resp = httpx.get(f"{self.base_url}/users",
            params={"page": page, "limit": limit}, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def create_user(self, name: str, email: str, role: str = "user") -> User:
        resp = httpx.post(f"{self.base_url}/users",
            json={"name": name, "email": email, "role": role}, headers=self._headers())
        resp.raise_for_status()
        data = resp.json()
        return User(**data)

    def get_user(self, user_id: str) -> User:
        resp = httpx.get(f"{self.base_url}/users/{user_id}", headers=self._headers())
        resp.raise_for_status()
        return User(**resp.json())

class AsyncAPIClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url, headers={"Authorization": f"Bearer {token}"})

    async def list_users(self, page: int = 1) -> dict:
        resp = await self.client.get("/users", params={"page": page})
        resp.raise_for_status()
        return resp.json()

    async def iter_all_users(self, page_size: int = 20) -> AsyncIterator[User]:
        page = 1
        while True:
            data = await self.list_users(page)
            for u in data["data"]:
                yield User(**u)
            if len(data["data"]) < page_size:
                break
            page += 1
```

## SDK Generation with OpenAPI Generator

```bash
# Generate TypeScript SDK
npx openapi-generator-cli generate \
  -i openapi.yaml -g typescript-fetch \
  -o sdk/typescript --additional-properties=supportsES6=true

# Generate Python SDK
npx openapi-generator-cli generate \
  -i openapi.yaml -g python \
  -o sdk/python --additional-properties=packageName=myapi_client

# Validate generated SDK against mock server
cd sdk/typescript && npm test
cd sdk/python && pytest
```

## SDK Test Against Mock

```javascript
describe('SDK', () => {
  const client = new APIClient({ baseUrl: 'http://localhost:4010', token: 'test' });

  it('lists users', async () => {
    const result = await client.listUsers();
    expect(result.data.length).toBeGreaterThan(0);
    expect(result.pagination.page).toBe(1);
  });

  it('creates user', async () => {
    const user = await client.createUser({ name: 'Test', email: 'test@example.com' });
    expect(user.id).toMatch(/^usr_/);
  });

  it('retries on 429', async () => {
    // Mock returns 429 first, then 200
    const user = await client.getUser('usr_test');
    expect(user.id).toBe('usr_test');
  });

  it('paginates all users', async () => {
    const all = [];
    for await (const user of client.listAllUsers(5)) {
      all.push(user);
    }
    expect(all.length).toBeGreaterThan(5);
  });
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
