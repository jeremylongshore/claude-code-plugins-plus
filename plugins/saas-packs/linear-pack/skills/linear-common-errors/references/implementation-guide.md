# Linear Common Errors - Implementation Guide

Detailed implementation examples and code patterns.

## Error Categories

### Authentication Errors (401/403)

#### Invalid API Key
```
Error: Authentication required
Code: UNAUTHENTICATED
```

**Causes:**
- API key is invalid, expired, or revoked
- Key format is incorrect (should start with `lin_api_`)
- Environment variable not loaded

**Solutions:**
```typescript
// Verify key format
const apiKey = process.env.LINEAR_API_KEY;
if (!apiKey?.startsWith("lin_api_")) {
  console.error("Invalid API key format");
}

// Test authentication
const client = new LinearClient({ apiKey });
try {
  await client.viewer;
  console.log("Authentication successful");
} catch (e) {
  console.error("Authentication failed:", e);
}
```

#### Permission Denied
```
Error: You don't have permission to access this resource
Code: FORBIDDEN
```

**Causes:**
- API key doesn't have required scope
- User not a member of the team/organization
- Resource belongs to different workspace

**Solutions:**
- Check API key permissions in Linear Settings > API
- Verify team membership
- Regenerate key with correct permissions

### Rate Limiting Errors (429)

```
Error: Rate limit exceeded
Code: RATE_LIMITED
Headers: X-RateLimit-Remaining: 0, Retry-After: 60
```

**Causes:**
- Too many requests in time window
- Burst of requests without throttling

**Solutions:**
```typescript
// Implement exponential backoff
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error: any) {
      if (error?.extensions?.code === "RATE_LIMITED" && i < maxRetries - 1) {
        const delay = Math.pow(2, i) * 1000;
        console.log(`Rate limited, retrying in ${delay}ms...`);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      throw error;
    }
  }
  throw new Error("Max retries exceeded");
}
```

### Validation Errors (400)

```
Error: Variable "$input" got invalid value
Code: BAD_USER_INPUT
```

**Common Validation Failures:**

| Field | Error | Fix |
|-------|-------|-----|
| `teamId` | "Team not found" | Verify team exists and accessible |
| `priority` | "Invalid priority" | Use 0-4 (0=None, 1=Urgent, 4=Low) |
| `estimate` | "Invalid estimate" | Use team's configured values |
| `stateId` | "State not found" | State must belong to same team |
| `assigneeId` | "User not found" | User must be team member |

**Debug Validation:**
```typescript
async function createIssueWithValidation(input: {
  teamId: string;
  title: string;
  stateId?: string;
  assigneeId?: string;
}) {
  // Validate team exists
  const team = await client.team(input.teamId);
  if (!team) throw new Error(`Team not found: ${input.teamId}`);

  // Validate state belongs to team
  if (input.stateId) {
    const states = await team.states();
    if (!states.nodes.find(s => s.id === input.stateId)) {
      throw new Error(`State ${input.stateId} not in team ${team.key}`);
    }
  }

  // Validate assignee is team member
  if (input.assigneeId) {
    const members = await team.members();
    if (!members.nodes.find(m => m.id === input.assigneeId)) {
      throw new Error(`User ${input.assigneeId} not in team ${team.key}`);
    }
  }

  return client.createIssue(input);
}
```

### GraphQL Errors

```
Error: Cannot query field "nonExistent" on type "Issue"
Code: GRAPHQL_VALIDATION_FAILED
```

**Causes:**
- Field name typo
- Querying deprecated field
- SDK version mismatch with API

**Solutions:**
```bash
# Update SDK to latest
npm update @linear/sdk

# Check API schema
curl -H "Authorization: $LINEAR_API_KEY" \
  https://api.linear.app/graphql \
  -d '{"query": "{ __schema { types { name } } }"}'
```

### Network Errors

```
Error: fetch failed
Cause: ECONNREFUSED / ETIMEDOUT
```

**Solutions:**
```typescript
// Add timeout and retry
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 30000);

try {
  const response = await fetch("https://api.linear.app/graphql", {
    signal: controller.signal,
    // ... other options
  });
} finally {
  clearTimeout(timeout);
}
```

## Diagnostic Commands

### Test API Connection
```bash
curl -s -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { name email } }"}' \
  https://api.linear.app/graphql | jq
```

### Check Rate Limit Status
```bash
curl -I -H "Authorization: $LINEAR_API_KEY" \
  https://api.linear.app/graphql
# Look for: X-RateLimit-Limit, X-RateLimit-Remaining
```

### Validate Webhook Signature
```typescript
import crypto from "crypto";

function verifyWebhookSignature(
  body: string,
  signature: string,
  secret: string
): boolean {
  const hmac = crypto.createHmac("sha256", secret);
  const digest = hmac.update(body).digest("hex");
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(digest)
  );
}
```

## Error Handling Pattern

```typescript
import { LinearClient, LinearError } from "@linear/sdk";

async function safeLinearCall<T>(
  operation: () => Promise<T>,
  context: string
): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    if (error instanceof LinearError) {
      console.error(`Linear API Error in ${context}:`, {
        message: error.message,
        type: error.type,
        errors: error.errors,
      });

      // Handle specific error types
      switch (error.type) {
        case "AuthenticationError":
          throw new Error("Please check your Linear API key");
        case "RateLimitedError":
          throw new Error("Too many requests, please retry later");
        default:
          throw error;
      }
    }
    throw error;
  }
}
```
