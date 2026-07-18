# ElevenLabs Install & Auth — Worked Examples

End-to-end walkthroughs for the two most common setup situations. Every code
block here is drawn from the same primitives shown in the SKILL.md skeleton and
[implementation.md](implementation.md).

## Example 1: New Node.js/TypeScript project

Install, wire the environment variable, and confirm auth in one pass.

```bash
# 1. Install the official SDK
npm install @elevenlabs/elevenlabs-js

# 2. Store the key in a git-ignored .env
echo 'ELEVENLABS_API_KEY=sk_your_key_here' >> .env
printf '.env\n.env.local\n.env.*.local\n' >> .gitignore
```

```typescript
// verify.ts — run with: npx tsx verify.ts
import "dotenv/config";
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

const client = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY,
});

const voices = await client.voices.getAll();
console.log(`Connected. ${voices.voices.length} voices available.`);
```

Expected output:

```
Connected. 20 voices available.
```

## Example 2: New Python project

```bash
# 1. Install the official SDK inside a virtualenv
python3 -m venv .venv && source .venv/bin/activate
pip install elevenlabs python-dotenv

# 2. Store the key
echo 'ELEVENLABS_API_KEY=sk_your_key_here' >> .env
printf '.env\n' >> .gitignore
```

```python
# verify.py — run with: python verify.py
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabsClient

load_dotenv()
client = ElevenLabsClient(api_key=os.environ.get("ELEVENLABS_API_KEY"))

voices = client.voices.get_all()
print(f"Connected. {len(voices.voices)} voices available.")
```

## Example 3: Confirm auth with no SDK (CI smoke test)

A single curl is enough to gate a pipeline on a valid, non-exhausted key:

```bash
curl -sf https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  | jq -e '.subscription.tier' \
  || { echo "ElevenLabs auth failed"; exit 1; }
```

A `401` here means the key is missing, malformed, or over quota — see the Error
Handling table in the SKILL.md.
