---
name: ideogram-install-auth
description: |
  Install and configure Ideogram API authentication.
  Use when setting up a new Ideogram integration, configuring API keys,
  or initializing Ideogram in your project.
  Trigger with phrases like "install ideogram", "setup ideogram",
  "ideogram auth", "configure ideogram API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, api, authentication, image-generation]

---
# Ideogram Install & Auth

## Overview
Set up Ideogram API authentication for AI image generation. Ideogram provides a REST API at `api.ideogram.ai` for text-to-image generation, editing, remixing, upscaling, and describing images. Authentication uses an `Api-Key` header on every request.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Ideogram account at [ideogram.ai](https://ideogram.ai)
- API key from Ideogram dashboard (Settings > API Beta)
- Payment method configured (auto top-up billing)

## Instructions

### Step 1: Get Your API Key
1. Log into [ideogram.ai](https://ideogram.ai)
2. Navigate to **Settings** (burger icon) > **API Beta**
3. Accept the Developer API Agreement
4. Click **Manage Payment** and add billing info via Stripe
5. Click **Create API key** -- store it immediately, it is shown only once

### Step 2: Install HTTP Client
```bash
set -euo pipefail
# Node.js (no SDK required -- Ideogram uses a plain REST API)
npm install dotenv

# Python
pip install requests python-dotenv
```

### Step 3: Configure Authentication
```bash
# Create .env file (NEVER commit to git)
echo 'IDEOGRAM_API_KEY=your-api-key-here' >> .env

# Add to .gitignore
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
```

### Step 4: Verify Connection
```typescript
// verify-ideogram.ts
import "dotenv/config";

async function verifyIdeogramAuth() {
  const response = await fetch("https://api.ideogram.ai/generate", {
    method: "POST",
    headers: {
      "Api-Key": process.env.IDEOGRAM_API_KEY!,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_request: {
        prompt: "A simple blue circle on white background",
        model: "V_2_TURBO",
        aspect_ratio: "ASPECT_1_1",
        magic_prompt_option: "OFF",
      },
    }),
  });

  if (response.ok) {
    const result = await response.json();
    console.log("Auth verified. Image URL:", result.data[0].url);
    console.log("Seed:", result.data[0].seed);
  } else {
    const err = await response.text();
    console.error(`Auth failed (${response.status}):`, err);
  }
}

verifyIdeogramAuth();
```

```python
# verify_ideogram.py
import os, requests
from dotenv import load_dotenv

load_dotenv()

response = requests.post(
    "https://api.ideogram.ai/generate",
    headers={
        "Api-Key": os.environ["IDEOGRAM_API_KEY"],
        "Content-Type": "application/json",
    },
    json={
        "image_request": {
            "prompt": "A simple blue circle on white background",
            "model": "V_2_TURBO",
            "aspect_ratio": "ASPECT_1_1",
            "magic_prompt_option": "OFF",
        }
    },
)

if response.ok:
    data = response.json()
    print("Auth verified. Image URL:", data["data"][0]["url"])
else:
    print(f"Auth failed ({response.status_code}):", response.text)
```

## API Base URLs

| API Version | Base URL | Notes |
|-------------|----------|-------|
| Legacy (V_2) | `https://api.ideogram.ai/generate` | JSON body with `image_request` wrapper |
| V3 Generate | `https://api.ideogram.ai/v1/ideogram-v3/generate` | Multipart form data |
| V3 Edit | `https://api.ideogram.ai/v1/ideogram-v3/edit` | Multipart form data |
| V3 Remix | `https://api.ideogram.ai/v1/ideogram-v3/remix` | Multipart form data |
| V3 Reframe | `https://api.ideogram.ai/v1/ideogram-v3/reframe` | Multipart form data |
| Upscale | `https://api.ideogram.ai/upscale` | Multipart form data |
| Describe | `https://api.ideogram.ai/describe` | Multipart form data |

## Billing Model
- Auto top-up: balance refills to $20 when it drops below $10 (configurable)
- Default rate limit: 10 in-flight requests
- Image URLs expire -- download immediately after generation
- Enterprise: contact `partnership@ideogram.ai` for higher limits

## Error Handling
| Error | HTTP Status | Cause | Solution |
|-------|-------------|-------|----------|
| Invalid API Key | 401 | Key missing or revoked | Verify key in dashboard, regenerate if needed |
| Rate Limited | 429 | Exceeded 10 in-flight requests | Queue requests, add backoff |
| Insufficient Credits | 402 | Balance depleted | Top up via dashboard billing |
| Safety Rejected | 422 | Prompt or image failed safety check | Rephrase prompt, remove flagged content |

## Output
- Environment variable `IDEOGRAM_API_KEY` configured
- `.env` file with key (git-ignored)
- Successful test generation confirming connectivity

## Resources
- [Ideogram Developer Docs](https://developer.ideogram.ai)
- [API Reference](https://developer.ideogram.ai/api-reference)
- [API Setup Guide](https://developer.ideogram.ai/ideogram-api/api-setup)
- [API Pricing](https://ideogram.ai/features/api-pricing)

## Next Steps
After successful auth, proceed to `ideogram-hello-world` for your first real generation.
