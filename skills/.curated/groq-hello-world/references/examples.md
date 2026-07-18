# Groq Hello World — Full Examples

Complete, copy-pasteable examples for streaming, Python, and model selection.
The lean first example lives in `SKILL.md`; the deeper variants below are moved
here so the main skill stays scannable.

## Streaming Response (TypeScript)

Stream tokens as they are generated instead of waiting for the full completion.
Useful for chat UIs and long generations where perceived latency matters.

```typescript
async function streamExample() {
  const stream = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [
      { role: "user", content: "Explain quantum computing in 3 sentences." },
    ],
    stream: true,
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || "";
    process.stdout.write(content);
  }
  console.log(); // newline
}
```

## Python Equivalent

The same request in Python using the official `groq` package. The API shape
mirrors the TypeScript SDK because both wrap the OpenAI-compatible endpoint.

```python
from groq import Groq

client = Groq()

completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Groq's LPU and why is it fast?"},
    ],
)

print(completion.choices[0].message.content)
print(f"Tokens: {completion.usage.total_tokens}")
```

## Try Different Models

Pick a model per task: the instant tier for high-throughput classification, the
versatile tier for reasoning and code, and the vision tier for multimodal input.

```typescript
// Speed tier -- fastest responses (~560 tok/s)
const fast = await groq.chat.completions.create({
  model: "llama-3.1-8b-instant",
  messages: [{ role: "user", content: "Hello!" }],
});

// Quality tier -- best reasoning (~280 tok/s)
const quality = await groq.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [{ role: "user", content: "Explain monads in Haskell." }],
});

// Vision tier -- multimodal understanding
const vision = await groq.chat.completions.create({
  model: "meta-llama/llama-4-scout-17b-16e-instruct",
  messages: [{
    role: "user",
    content: [
      { type: "text", text: "Describe this image." },
      { type: "image_url", image_url: { url: "https://example.com/photo.jpg" } },
    ],
  }],
});
```
