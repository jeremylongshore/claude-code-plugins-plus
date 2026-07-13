# Environment Setup

## Environment Setup

### Environment Variables

```bash
# .env file
KLINGAI_API_KEY=your-api-key-here
KLINGAI_BASE_URL=https://api.klingai.com/v1

# Shell export
export KLINGAI_API_KEY="your-api-key-here"
```

### Python Setup

```python
import os
import requests

KLINGAI_API_KEY = os.environ.get("KLINGAI_API_KEY")
KLINGAI_BASE_URL = "https://api.klingai.com/v1"

headers = {
    "Authorization": f"Bearer {KLINGAI_API_KEY}",
    "Content-Type": "application/json"
}

def create_video(prompt: str, duration: int = 5):
    response = requests.post(
        f"{KLINGAI_BASE_URL}/videos/text2video",
        headers=headers,
        json={"prompt": prompt, "duration": duration}
    )
    return response.json()
```

### TypeScript/Node Setup

```typescript
import axios from 'axios';

const KLINGAI_API_KEY = process.env.KLINGAI_API_KEY;
const KLINGAI_BASE_URL = 'https://api.klingai.com/v1';

const klingaiClient = axios.create({
  baseURL: KLINGAI_BASE_URL,
  headers: {
    'Authorization': `Bearer ${KLINGAI_API_KEY}`,
    'Content-Type': 'application/json'
  }
});

async function createVideo(prompt: string, duration: number = 5) {
  const response = await klingaiClient.post('/videos/text2video', {
    prompt,
    duration
  });
  return response.data;
}
```
