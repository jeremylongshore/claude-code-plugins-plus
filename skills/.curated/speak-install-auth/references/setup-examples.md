# Speak Install & Auth Setup Examples

## TypeScript Setup with Speech Recognition

```typescript
import { SpeakClient, SpeechRecognizer } from '@speak/language-sdk';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  language: 'es',
});

const recognizer = new SpeechRecognizer(client, {
  onSpeechResult: (result) => {
    console.log('User said:', result.transcript);
    console.log('Pronunciation score:', result.pronunciationScore);
  },
  onError: (error) => console.error('Speech error:', error),
});
```

## Python Setup

```python
import os
from speak_sdk import SpeakClient, LessonSession

client = SpeakClient(
    api_key=os.environ.get('SPEAK_API_KEY'),
    app_id=os.environ.get('SPEAK_APP_ID'),
    language='ja'  # Japanese
)

# Verify connection
status = client.health.check()
print(f"Connected: {status.healthy}")
```

## Alternative: OpenAI-Compatible API

Speak uses the OpenAI real-time API under the hood. Install the OpenAI SDK as an alternative:

```bash
npm install openai
```

## Supported Languages

| Language | Code | Status |
|----------|------|--------|
| English | en | Available |
| Spanish | es | Available |
| French | fr | Available |
| German | de | Available |
| Portuguese (BR) | pt-BR | Available |
| Korean | ko | Available |
| Japanese | ja | Available |
| Mandarin (Traditional) | zh-TW | Available |
| Mandarin (Simplified) | zh-CN | Available |
| Indonesian | id | Available |

## Token Expiration

- Default token validity: depends on API key type
- Implement token refresh for long-running sessions
- Store credentials securely using environment variables or a secrets manager
