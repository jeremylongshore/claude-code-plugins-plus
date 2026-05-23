# Web Framework Integration

## Web Framework Integration

### FastAPI Streaming

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def generate_stream(prompt: str, model: str):
    """Generator for StreamingResponse."""
    stream = await async_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

@app.post("/chat/stream")
async def chat_stream(prompt: str, model: str = "openai/gpt-4-turbo"):
    return StreamingResponse(
        generate_stream(prompt, model),
        media_type="text/plain"
    )
```

### Flask SSE Streaming

```python
from flask import Flask, Response, request

app = Flask(__name__)

def generate_sse(prompt: str, model: str):
    """Generate Server-Sent Events."""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            # SSE format
            yield f"data: {content}\n\n"

    yield "data: [DONE]\n\n"

@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    data = request.json
    return Response(
        generate_sse(data["prompt"], data.get("model", "openai/gpt-4-turbo")),
        mimetype="text/event-stream"
    )
```

### Express.js SSE

```typescript
import express from 'express';

const app = express();
app.use(express.json());

app.post('/chat/stream', async (req, res) => {
  const { prompt, model = 'openai/gpt-4-turbo' } = req.body;

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const stream = await client.chat.completions.create({
    model,
    messages: [{ role: 'user', content: prompt }],
    stream: true,
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    if (content) {
      res.write(`data: ${JSON.stringify({ content })}\n\n`);
    }
  }

  res.write('data: [DONE]\n\n');
  res.end();
});
```
