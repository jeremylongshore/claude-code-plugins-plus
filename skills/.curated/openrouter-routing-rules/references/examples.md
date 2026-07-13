# OpenRouter Routing Rules Examples

## Priority-Based Routing

```typescript
const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'anthropic/claude-3-5-sonnet',
    messages: [{ role: 'user', content: 'Hello' }],
    route: 'fallback',  // Try primary, fall back to next available
  }),
});
```

## Cost-Constrained Routing

```typescript
// Only use models under $0.01/1k tokens
const costConstrainedRequest = {
  model: 'openai/gpt-4o-mini',
  messages,
  route: 'price',  // Route to cheapest available provider
  max_price: { prompt: '0.01', completion: '0.01' },
};
```

## Conditional Routing by Prompt Content

```typescript
function routeByComplexity(prompt: string): string {
  const wordCount = prompt.split(' ').length;
  if (wordCount > 500) return 'anthropic/claude-3-5-sonnet';   // Long context
  if (wordCount > 100) return 'openai/gpt-4o-mini';             // Medium
  return 'meta-llama/llama-3.1-8b-instruct:free';               // Short/simple
}

const model = routeByComplexity(userPrompt);
const response = await openrouterClient.chat.completions.create({ model, messages });
```

## Latency-Optimized Routing

```typescript
// Route to fastest provider (not cheapest)
const fastRequest = {
  model: 'openai/gpt-4o',
  messages,
  provider: { order: ['OpenAI', 'Azure'], allow_fallbacks: true },
};
```

## A/B Testing Routing

```typescript
function abRoute(userId: string): string {
  const bucket = parseInt(userId.slice(-1), 16) % 2;
  return bucket === 0 ? 'anthropic/claude-3-haiku' : 'openai/gpt-4o-mini';
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
