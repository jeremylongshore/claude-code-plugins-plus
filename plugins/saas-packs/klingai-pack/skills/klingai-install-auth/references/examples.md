# Kling AI Install & Auth -- Examples

## Environment Setup

```bash
# Set API credentials
export KLING_API_KEY="your-kling-api-key-here"
export KLING_ACCESS_KEY_ID="your-access-key-id"
export KLING_ACCESS_KEY_SECRET="your-access-key-secret"

# Verify the key is set
echo "Key length: ${#KLING_API_KEY}"
```

## Python Authentication with JWT

```python
import os
import time
import jwt  # pip install PyJWT


KLING_ACCESS_KEY_ID = os.environ["KLING_ACCESS_KEY_ID"]
KLING_ACCESS_KEY_SECRET = os.environ["KLING_ACCESS_KEY_SECRET"]
KLING_API_BASE = "https://api.klingai.com"


def generate_kling_token(expiry_seconds: int = 1800) -> str:
    """Generate a signed JWT token for Kling AI API authentication."""
    now = int(time.time())
    payload = {
        "iss": KLING_ACCESS_KEY_ID,
        "exp": now + expiry_seconds,
        "nbf": now - 5,  # Allow 5s clock skew
    }
    return jwt.encode(payload, KLING_ACCESS_KEY_SECRET, algorithm="HS256")


def get_auth_headers() -> dict:
    """Return headers with a fresh JWT token for Kling AI requests."""
    token = generate_kling_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
```

## Test Authentication

```python
import json
import urllib.request
import urllib.error


def verify_kling_auth() -> dict:
    """Verify Kling AI API access by calling the account endpoint."""
    headers = get_auth_headers()
    req = urllib.request.Request(
        f"{KLING_API_BASE}/v1/account",
        headers=headers,
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            print(f"[OK] Authenticated as: {data.get('name', 'unknown')}")
            return data
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise RuntimeError("Authentication failed: check KLING_ACCESS_KEY_ID and KLING_ACCESS_KEY_SECRET")
        raise RuntimeError(f"API error: HTTP {e.code}")


if __name__ == "__main__":
    result = verify_kling_auth()
    print(json.dumps(result, indent=2))
```

## TypeScript Authentication

```typescript
import * as jwt from 'jsonwebtoken';
import fetch from 'node-fetch';

const ACCESS_KEY_ID = process.env.KLING_ACCESS_KEY_ID!;
const ACCESS_KEY_SECRET = process.env.KLING_ACCESS_KEY_SECRET!;

function generateToken(expirySeconds = 1800): string {
    return jwt.sign(
        { iss: ACCESS_KEY_ID },
        ACCESS_KEY_SECRET,
        {
            algorithm: 'HS256',
            expiresIn: expirySeconds,
            notBefore: -5,
        }
    );
}

function getHeaders(): Record<string, string> {
    return {
        Authorization: `Bearer ${generateToken()}`,
        'Content-Type': 'application/json',
    };
}

async function verifyAuth(): Promise<void> {
    const resp = await fetch('https://api.klingai.com/v1/account', {
        headers: getHeaders(),
    });
    if (!resp.ok) {
        throw new Error(`Auth failed: HTTP ${resp.status}`);
    }
    const data = await resp.json();
    console.log('Authenticated:', data);
}

verifyAuth().catch(console.error);
```

## First API Call: Text-to-Video Generation

```python
def generate_video(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    model: str = "kling-v1",
) -> str:
    """Submit a text-to-video generation request and return the task ID."""
    headers = get_auth_headers()
    payload = {
        "model_name": model,
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "cfg_scale": 0.5,
        "mode": "std",
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{KLING_API_BASE}/v1/videos/text2video",
        data=body,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    task_id = data["data"]["task_id"]
    print(f"Video generation started: task_id={task_id}")
    return task_id


# Usage
task_id = generate_video(
    prompt="A serene mountain lake at sunrise with mist rising off the water",
    duration=5,
    aspect_ratio="16:9",
)
print(f"Poll status at: GET /v1/videos/text2video/{task_id}")
```

## Resources

- [Kling AI Developer Portal](https://klingai.com/developer)
- [Kling AI API Reference](https://docs.klingai.com/api-reference)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
