# ElevenLabs Install & Auth — Full Implementation

Complete client initialization and connection-verification code for both
runtimes, plus the raw-API equivalent. The SKILL.md carries the lean skeleton;
this file is the full-depth walkthrough.

## Initialize the Client

**TypeScript:**

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

const client = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY,
  // Optional: configure retries (default: 2)
  maxRetries: 3,
  // Optional: configure timeout in seconds
  timeoutInSeconds: 30,
});
```

**Python:**

```python
import os
from elevenlabs.client import ElevenLabsClient

client = ElevenLabsClient(
    api_key=os.environ.get("ELEVENLABS_API_KEY")
)
```

## Verify Connection

**TypeScript:**

```typescript
async function verifyConnection() {
  // List available voices to confirm auth works
  const voices = await client.voices.getAll();
  console.log(`Connected. ${voices.voices.length} voices available.`);

  // Check subscription/quota
  const user = await client.user.get();
  console.log(`Plan: ${user.subscription.tier}`);
  console.log(`Characters used: ${user.subscription.character_count}/${user.subscription.character_limit}`);
}

verifyConnection().catch(console.error);
```

**Python:**

```python
def verify_connection():
    voices = client.voices.get_all()
    print(f"Connected. {len(voices.voices)} voices available.")

    user = client.user.get()
    print(f"Plan: {user.subscription.tier}")
    print(f"Characters used: {user.subscription.character_count}/{user.subscription.character_limit}")

verify_connection()
```

**cURL (raw API):**

```bash
curl -s https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | jq '.subscription.tier'
```

## API Key Best Practices

- Never hardcode keys in source files
- Use separate keys for dev/staging/prod
- Rotate keys quarterly via the dashboard
- The `xi-api-key` header is used for REST calls; SDKs handle this automatically
- Free tier: 10,000 characters/month, Starter: 30,000, Creator: 100,000
