# Install & Auth Examples

## Environment Setup

```bash
# Add to your .env file
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Or export directly
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Verify the variable is set
echo "Key starts with: ${OPENROUTER_API_KEY:0:8}..."
```

## Python — Initialize Client and Verify Auth

```python
import os
from openai import OpenAI, AuthenticationError

def create_openrouter_client() -> OpenAI:
    """Create and verify an OpenRouter client."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    if not api_key.startswith("sk-or-"):
        raise ValueError("Invalid key format — must start with 'sk-or-'")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://your-app.com",
            "X-Title": "Your App Name",
        },
    )

def verify_auth(client: OpenAI) -> bool:
    """Send a minimal request to verify authentication."""
    try:
        response = client.chat.completions.create(
            model="google/gemma-2-9b-it:free",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1,
        )
        print(f"Auth OK — used model: {response.model}")
        return True
    except AuthenticationError as e:
        print(f"Auth failed: {e.message}")
        return False

client = create_openrouter_client()
verify_auth(client)
```

## TypeScript — Initialize Client and Verify Auth

```typescript
import OpenAI from "openai";

function createClient(): OpenAI {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) throw new Error("OPENROUTER_API_KEY not set");
  if (!apiKey.startsWith("sk-or-"))
    throw new Error("Invalid key format — must start with 'sk-or-'");

  return new OpenAI({
    baseURL: "https://openrouter.ai/api/v1",
    apiKey,
    defaultHeaders: {
      "HTTP-Referer": "https://your-app.com",
      "X-Title": "Your App Name",
    },
  });
}

async function verifyAuth(client: OpenAI): Promise<boolean> {
  try {
    const res = await client.chat.completions.create({
      model: "google/gemma-2-9b-it:free",
      messages: [{ role: "user", content: "Hi" }],
      max_tokens: 1,
    });
    console.log(`Auth OK — model: ${res.model}`);
    return true;
  } catch (err: any) {
    console.error(`Auth failed: ${err.message}`);
    return false;
  }
}

const client = createClient();
verifyAuth(client);
```

## cURL — Check Key and Credit Balance

```bash
# Verify key is valid by checking credits
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq .

# Expected response:
# {
#   "data": {
#     "label": "My App Key",
#     "usage": 0.0023,
#     "limit": 10,
#     "is_free_tier": false,
#     "rate_limit": { "requests": 200, "interval": "10s" }
#   }
# }
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
