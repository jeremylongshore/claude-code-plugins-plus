# Typescript Interfaces

## TypeScript Interfaces

```typescript
// User types
interface User {
  id: string;
  email: string;
  name: string | null;
  createdAt: string;
}

interface CreateUserRequest {
  email: string;
  password: string;
  name?: string;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface AuthResponse {
  user: User;
  token: string;
  expiresAt: string;
}

// Error response
interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string[]>;
}
```

```

### Type Guidelines

- Use explicit types, not `any`
- Mark optional fields with `?`
- Use union types for nullable: `string | null`
- Include all possible response shapes
- Match types to JSON serialization
