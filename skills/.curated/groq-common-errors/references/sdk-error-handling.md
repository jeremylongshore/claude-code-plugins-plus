# SDK-Specific Error Handling

Groq's official SDKs raise typed exceptions so you can branch on the failure class instead of parsing status codes by hand. These patterns are the deep companion to the `groq-common-errors` skill.

## TypeScript

```typescript
import Groq from "groq-sdk";

try {
  await groq.chat.completions.create({ /* ... */ });
} catch (err) {
  if (err instanceof Groq.APIError) {
    console.error(`Status: ${err.status}, Message: ${err.message}`);
  } else if (err instanceof Groq.APIConnectionError) {
    console.error("Network error:", err.message);
  } else if (err instanceof Groq.RateLimitError) {
    console.error("Rate limited:", err.message);
  } else if (err instanceof Groq.AuthenticationError) {
    console.error("Auth failed:", err.message);
  }
}
```

## Python

```python
from groq import Groq, APIError, RateLimitError, AuthenticationError

try:
    client.chat.completions.create(...)
except RateLimitError as e:
    print(f"Rate limited: {e.message}")
except AuthenticationError as e:
    print(f"Auth error: {e.message}")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## Escalation Path

1. Check [status.groq.com](https://status.groq.com) for ongoing incidents
2. Collect request ID from error response (`x-request-id` header)
3. Run `groq-debug-bundle` skill to gather diagnostics
4. Contact Groq support with request ID and debug bundle
