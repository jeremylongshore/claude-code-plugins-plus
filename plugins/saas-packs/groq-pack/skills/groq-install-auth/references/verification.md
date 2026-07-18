# Verifying the Groq Connection

After installing the SDK and setting `GROQ_API_KEY`, run one of these scripts to
confirm the key is valid and the SDK can reach GroqCloud. Both list the models
your key can access — a successful list proves authentication end-to-end.

## Verify Connection (TypeScript)

```typescript
import Groq from "groq-sdk";

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
});

async function verify() {
  const models = await groq.models.list();
  console.log("Connected! Available models:");
  for (const model of models.data) {
    console.log(`  ${model.id} (owned by ${model.owned_by})`);
  }
}

verify().catch(console.error);
```

## Verify Connection (Python)

```python
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

models = client.models.list()
print("Connected! Available models:")
for model in models.data:
    print(f"  {model.id} (owned by {model.owned_by})")
```

## Expected output

A successful run prints one line per model, for example:

```
Connected! Available models:
  llama-3.3-70b-versatile (owned by Meta)
  llama-3.1-8b-instant (owned by Meta)
  ...
```

If instead you see a `401 Invalid API Key` error, the key is missing, revoked, or
mistyped — see [troubleshooting.md](troubleshooting.md).
