# Typescript Example

## TypeScript Example

### Basic Request

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY,
});

async function main() {
  const response = await client.chat.completions.create({
    model: 'openai/gpt-3.5-turbo',
    messages: [
      { role: 'user', content: 'Say hello!' }
    ],
  });

  console.log(response.choices[0].message.content);
}

main();
```

### With Streaming

```typescript
const stream = await client.chat.completions.create({
  model: 'openai/gpt-4-turbo',
  messages: [{ role: 'user', content: 'Write a poem' }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}
```
