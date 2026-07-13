# API Contract Generation Examples

## OpenAPI 3.1 Specification

```yaml
openapi: 3.1.0
info:
  title: User Management API
  version: 2.0.0
servers:
  - url: https://api.example.com/v2

paths:
  /users:
    get:
      operationId: listUsers
      summary: List users with pagination
      parameters:
        - name: page
          in: query
          schema: { type: integer, minimum: 1, default: 1 }
        - name: limit
          in: query
          schema: { type: integer, minimum: 1, maximum: 100, default: 20 }
      responses:
        '200':
          description: Paginated user list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
    post:
      operationId: createUser
      security: [{ bearerAuth: [] }]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/ValidationError'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    User:
      type: object
      required: [id, name, email, status]
      properties:
        id: { type: string, pattern: '^usr_[a-zA-Z0-9]+$' }
        name: { type: string, minLength: 1, maxLength: 255 }
        email: { type: string, format: email }
        status: { type: string, enum: [active, inactive, suspended] }
    CreateUserRequest:
      type: object
      required: [name, email]
      properties:
        name: { type: string, minLength: 1, maxLength: 255 }
        email: { type: string, format: email }
        role: { type: string, enum: [user, admin], default: user }
```

## Pact Consumer Contract Test

```javascript
// tests/contract/consumer/user-api.pact.js
const { PactV3, MatchersV3 } = require('@pact-foundation/pact');
const { like, eachLike, regex } = MatchersV3;

const provider = new PactV3({ consumer: 'frontend-app', provider: 'user-service' });

describe('User API Contract', () => {
  it('lists users', async () => {
    await provider
      .given('users exist')
      .uponReceiving('a request to list users')
      .withRequest({
        method: 'GET',
        path: '/users',
        query: { page: '1', limit: '20' },
        headers: { Authorization: regex(/^Bearer .+$/, 'Bearer token123') },
      })
      .willRespondWith({
        status: 200,
        body: {
          data: eachLike({ id: like('usr_abc'), name: like('Alice'), email: like('a@b.com') }),
          pagination: { page: like(1), limit: like(20), total: like(100) },
        },
      })
      .executeTest(async (mockServer) => {
        const res = await fetch(`${mockServer.url}/users?page=1&limit=20`, {
          headers: { Authorization: 'Bearer token123' },
        });
        expect(res.status).toBe(200);
        const body = await res.json();
        expect(body.data.length).toBeGreaterThan(0);
      });
  });

  it('rejects invalid create request', async () => {
    await provider
      .uponReceiving('an invalid create user request')
      .withRequest({
        method: 'POST', path: '/users',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer token123' },
        body: { name: '' },
      })
      .willRespondWith({
        status: 400,
        body: {
          type: like('https://api.example.com/errors/validation'),
          title: like('Validation Error'),
          status: 400,
          errors: eachLike({ field: like('email'), message: like('Required') }),
        },
      })
      .executeTest(async (mockServer) => {
        const res = await fetch(`${mockServer.url}/users`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: 'Bearer token123' },
          body: JSON.stringify({ name: '' }),
        });
        expect(res.status).toBe(400);
      });
  });
});
```

## Spectral Linting Configuration

```yaml
# .spectral.yaml
extends: spectral:oas
rules:
  operation-operationId:
    severity: error
  oas3-valid-schema-example:
    severity: error
  path-casing:
    severity: warn
    given: "$.paths[*]~"
    then:
      function: casing
      functionOptions: { type: kebab }
```

## Provider Verification

```javascript
const { Verifier } = require('@pact-foundation/pact');

it('satisfies consumer contracts', async () => {
  await new Verifier({
    providerBaseUrl: 'http://localhost:3000',
    pactUrls: ['./contracts/pact/frontend-app-user-service.json'],
    stateHandlers: {
      'users exist': async () => {
        await db.users.bulkCreate([
          { name: 'Alice', email: 'alice@example.com', status: 'active' },
        ]);
      },
    },
  }).verifyProvider();
});
```

## Contract Generation Script

```bash
#!/bin/bash
npx @stoplight/spectral-cli lint openapi.yaml --fail-severity warn
npx swagger-cli validate openapi.yaml
npx openapi-to-postmanv2 -s openapi.yaml -o contracts/postman/collection.json
npx jest tests/contract/consumer/ --verbose
npx jest tests/contract/provider/ --verbose
echo "All contract checks passed"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
