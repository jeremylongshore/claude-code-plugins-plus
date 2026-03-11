# Mistral AI Reference Architecture - Implementation Details

## Client Wrapper
```typescript
import Mistral from '@mistralai/mistralai';
let instance: Mistral | null = null;
export function getMistralClient(): Mistral {
  if (!instance) {
    const config = getMistralConfig();
    instance = new Mistral({ apiKey: config.apiKey, timeout: config.timeout });
  }
  return instance;
}
```

## Configuration Management (Zod)
```typescript
const configSchema = z.object({
  apiKey: z.string().min(1),
  model: z.string().default('mistral-small-latest'),
  timeout: z.number().default(30000),
  maxRetries: z.number().default(3),
  cache: z.object({ enabled: z.boolean().default(true), ttlSeconds: z.number().default(300) }).default({}),
});
```

## Error Handling
```typescript
export function wrapMistralError(error: unknown): MistralServiceError {
  if (err.status === 429) return new MistralServiceError('Rate limit exceeded', 'RATE_LIMIT', 429, true, err);
  if (err.status === 401) return new MistralServiceError('Authentication failed', 'AUTH_ERROR', 401, false, err);
  if (err.status >= 500) return new MistralServiceError('Mistral service error', 'SERVICE_ERROR', err.status, true, err);
  return new MistralServiceError(err.message || 'Unknown error', 'UNKNOWN', err.status, false, err);
}
```

## Chat Service with Caching
```typescript
export class ChatService {
  async complete(messages, options = {}) {
    if (options.useCache && options.temperature === 0) {
      const cached = await cache.get(messages, model);
      if (cached) return cached;
    }
    const response = await withRetry(() => client.chat.complete({ model, messages, temperature: options.temperature, maxTokens: options.maxTokens }));
    return response.choices?.[0]?.message?.content ?? '';
  }

  async *stream(messages, options = {}) {
    const stream = await client.chat.stream({ model, messages });
    for await (const event of stream) {
      const content = event.data?.choices?.[0]?.delta?.content;
      if (content) yield content;
    }
  }
}
```

## Health Check
```typescript
export async function checkMistralHealth(): Promise<HealthStatus> {
  const start = Date.now();
  try { await getMistralClient().models.list(); return { status: 'healthy', latencyMs: Date.now() - start }; }
  catch (error: any) { return { status: 'unhealthy', latencyMs: Date.now() - start, error: error.message }; }
}
```

## Prompt Templates
```typescript
export const templates = {
  summarize: { system: 'You create concise summaries.', user: ({ text, maxWords }) => `Summarize in ${maxWords} words:\n\n${text}` },
  classify: { system: 'Respond with only the category name.', user: ({ text, categories }) => `Classify into: ${categories}\n\nText: ${text}` },
  codeReview: { system: 'Expert code reviewer. Be concise.', user: ({ code, language }) => `Review this ${language} code:\n\n\`\`\`${language}\n${code}\n\`\`\`` },
};
```
