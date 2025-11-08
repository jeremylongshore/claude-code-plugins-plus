# API Test Automation Plugin

Automated API endpoint testing with intelligent test generation, validation, and comprehensive coverage for REST and GraphQL APIs.

## Features

- **REST API testing** - Complete CRUD operation coverage
- **GraphQL testing** - Queries, mutations, subscriptions
- **Authentication** - Multiple auth methods (Bearer, OAuth, API keys)
- **Contract testing** - Validate against OpenAPI/Swagger specs
- **Automatic test generation** - Analyze endpoints and generate tests
- **Comprehensive validation** - Status codes, headers, body structure
- **Performance testing** - Response time assertions
- **Security testing** - Auth bypass, injection attempts

## Installation

```bash
/plugin install api-test-automation@claude-code-plugins-plus
```

## Usage

The API testing agent activates automatically when you mention API testing needs. You can also invoke directly:

### Generate tests for REST API

```
Generate API tests for the user management endpoints in src/routes/users.js
```

### Test GraphQL API

```
Create GraphQL API tests for the product queries and mutations
```

### Validate against OpenAPI spec

```
Generate contract tests validating against openapi.yaml
```

### Test authentication flows

```
Create tests for JWT authentication including login, refresh, and protected endpoints
```

## What Gets Generated

### 1. Complete Test Suites

```javascript
// RESTful API test example
describe('User API', () => {
  // Authentication tests
  describe('POST /api/auth/login', () => {
    it('should return JWT token with valid credentials', async () => {
      const response = await api.post('/api/auth/login', {
        email: '[email protected]',
        password: 'password123'
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('token');
      expect(response.data).toHaveProperty('user');
      expect(response.data.user.email).toBe('[email protected]');
    });

    it('should return 401 with invalid credentials', async () => {
      const response = await api.post('/api/auth/login', {
        email: '[email protected]',
        password: 'wrongpassword'
      });

      expect(response.status).toBe(401);
      expect(response.data.error).toBe('Invalid credentials');
    });
  });

  // CRUD operations
  describe('GET /api/users', () => {
    it('should require authentication', async () => {
      const response = await api.get('/api/users');
      expect(response.status).toBe(401);
    });

    it('should return user list with valid token', async () => {
      const response = await api.get('/api/users', {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(Array.isArray(response.data)).toBe(true);
      expect(response.data[0]).toHaveProperty('id');
      expect(response.data[0]).toHaveProperty('email');
    });
  });

  describe('POST /api/users', () => {
    it('should create user with valid data', async () => {
      const newUser = {
        email: '[email protected]',
        name: 'John Doe',
        role: 'user'
      };

      const response = await api.post('/api/users', newUser, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });

      expect(response.status).toBe(201);
      expect(response.data.email).toBe(newUser.email);
      expect(response.data).toHaveProperty('id');
    });

    it('should validate required fields', async () => {
      const response = await api.post('/api/users', {}, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });

      expect(response.status).toBe(400);
      expect(response.data.errors).toContain('email');
    });
  });
});
```

### 2. Authentication Helpers

```javascript
// Authentication utility functions
async function loginUser(email, password) {
  const response = await api.post('/api/auth/login', { email, password });
  return response.data.token;
}

async function createTestUser(role = 'user') {
  const user = {
    email: `test-${Date.now()}@example.com`,
    password: 'test123',
    role
  };
  await api.post('/api/users', user, { headers: { Authorization: adminToken } });
  return loginUser(user.email, user.password);
}
```

### 3. Test Data Factories

```javascript
// Factory functions for test data
const userFactory = {
  valid: () => ({
    email: `user-${Date.now()}@example.com`,
    name: 'Test User',
    password: 'securePassword123'
  }),

  invalid: () => ({
    email: 'invalid-email',
    name: '',
    password: '123' // Too short
  })
};
```

### 4. GraphQL Tests

```javascript
describe('GraphQL API', () => {
  describe('Query: user', () => {
    it('should fetch user by ID', async () => {
      const query = `
        query GetUser($id: ID!) {
          user(id: $id) {
            id
            email
            name
          }
        }
      `;

      const response = await graphql.query(query, { id: userId });

      expect(response.errors).toBeUndefined();
      expect(response.data.user.id).toBe(userId);
    });
  });

  describe('Mutation: createUser', () => {
    it('should create new user', async () => {
      const mutation = `
        mutation CreateUser($input: CreateUserInput!) {
          createUser(input: $input) {
            id
            email
          }
        }
      `;

      const response = await graphql.mutate(mutation, {
        input: { email: '[email protected]', name: 'New User' }
      });

      expect(response.errors).toBeUndefined();
      expect(response.data.createUser).toHaveProperty('id');
    });
  });
});
```

## Test Coverage

The agent generates tests for:

### Success Scenarios
- Valid requests with proper authentication
- Correct data formats and required fields
- Expected response structures

### Error Scenarios
- Missing or invalid authentication
- Validation errors (bad data formats)
- Missing required fields
- Unauthorized access (wrong permissions)
- Resource not found (404)
- Conflict errors (409, duplicates)

### Edge Cases
- Empty request bodies
- Null/undefined values
- Boundary values (min/max lengths)
- Special characters in inputs
- Large payloads

### Performance
- Response time thresholds
- Payload size validation
- Concurrent request handling

## Best Practices Applied

- **Descriptive test names** - Clear what is tested and expected
- **Test isolation** - No dependencies between tests
- **Proper cleanup** - Delete test data after tests
- **Authentication management** - Reusable auth helpers
- **Data factories** - Generate test data dynamically
- **Comprehensive assertions** - Validate all critical fields
- **Error testing** - Both success and failure paths
- **Documentation** - Comments for complex scenarios

## Requirements

- Claude Code CLI
- HTTP client library (axios, requests, etc.)
- Testing framework (Jest, pytest, RSpec, etc.)
- API access (local or test environment)

## Configuration

Create API test configuration:

```json
{
  "baseURL": "http://localhost:3000/api",
  "timeout": 5000,
  "auth": {
    "type": "bearer",
    "tokenEndpoint": "/auth/login"
  },
  "testUsers": {
    "admin": {
      "email": "[email protected]",
      "password": "admin123"
    },
    "user": {
      "email": "[email protected]",
      "password": "user123"
    }
  }
}
```

## Tips

1. **Start with happy paths** - Ensure basic functionality works
2. **Test authentication first** - Auth issues block other tests
3. **Use realistic test data** - Match production data patterns
4. **Check response times** - Add performance assertions
5. **Test error messages** - Verify helpful error responses
6. **Validate data types** - Not just presence, but correct types
7. **Clean up test data** - Prevent database pollution

## License

MIT
