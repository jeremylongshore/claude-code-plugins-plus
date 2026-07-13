# Drop-In Replacement

## Drop-in Replacement

### The Key Insight

```
OpenRouter is OpenAI API compatible.
Change base URL and API key, keep everything else.
```

### Python Migration

```python
# Before (OpenAI direct)
from openai import OpenAI

client = OpenAI(
    api_key="sk-..."  # OpenAI key
)

# After (OpenRouter)
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-..."  # OpenRouter key
)

# Code stays exactly the same!
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",  # Add provider prefix
    messages=[{"role": "user", "content": "Hello"}]
)
```

### TypeScript Migration

```typescript
// Before (OpenAI direct)
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-...',
});

// After (OpenRouter)
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: 'sk-or-...',
});

// Same code works!
const response = await client.chat.completions.create({
  model: 'openai/gpt-4-turbo',  // Add provider prefix
  messages: [{ role: 'user', content: 'Hello' }],
});
```
