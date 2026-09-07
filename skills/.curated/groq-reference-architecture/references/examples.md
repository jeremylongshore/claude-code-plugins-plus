# Groq Reference Architecture — Worked Examples

These examples compose the building blocks defined in
[implementation.md](implementation.md) — `selectModel`, `completionWithMiddleware`,
`completionWithFallback`, and `streamCompletion` — into the request shapes an
application layer actually issues.

## Example 1: Latency-critical chat turn

Route to the speed tier and return a single completion.

```typescript
import Groq from "groq-sdk";
import { selectModel } from "./groq/router";
import { completionWithMiddleware } from "./groq/middleware";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

const model = selectModel({ maxLatencyMs: 80, costSensitive: true });
// → llama-3.1-8b-instant

const res = await completionWithMiddleware(groq, model.id, [
  { role: "user", content: "Summarize this ticket in one line." },
]);
console.log(res.choices[0].message.content);
```

## Example 2: Quality request with fallback protection

Let the router pick the quality tier, but wrap the call so a 429/5xx drops to a
model in a different rate-limit pool before degrading gracefully.

```typescript
import { selectModel } from "./groq/router";
import { completionWithFallback } from "./groq/fallback";

const model = selectModel({ needsTools: true });   // → llama-3.3-70b-versatile

const res = await completionWithFallback(groq, [
  { role: "user", content: "Extract the invoice total and due date." },
], { primaryModel: model.id });
```

## Example 3: Streaming a chat UI

Consume the async generator token-by-token for a real-time SSE surface.

```typescript
import { streamCompletion } from "./groq/streaming";

for await (const event of streamCompletion(groq, [
  { role: "user", content: "Explain LPU inference in two sentences." },
])) {
  if (event.type === "token") process.stdout.write(event.content!);
  else if (event.type === "error") console.error(event.error);
}
```

## Example 4: Vision request routing

A request that carries an image auto-routes to the vision-capable model.

```typescript
const model = selectModel({ needsVision: true });
// → meta-llama/llama-4-scout-17b-16e-instruct
```
