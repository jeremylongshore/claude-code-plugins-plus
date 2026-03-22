---
name: langchain-deploy-integration
description: |
  Deploy LangChain applications to production with LangServe,
  Docker, and cloud platforms (Cloud Run, AWS Lambda).
  Trigger: "deploy langchain", "langchain production deploy",
  "langchain docker", "langchain cloud run", "LangServe".
allowed-tools: Read, Write, Edit, Bash(docker:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, deployment, docker]

---
# LangChain Deploy Integration

## Overview

Deploy LangChain chains and agents as APIs using LangServe (Python) or custom Express/Fastify servers (Node.js). Covers containerization, cloud deployment, health checks, and production observability.

## Option A: LangServe API (Python)

```python
# serve.py
from fastapi import FastAPI
from langserve import add_routes
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

app = FastAPI(title="LangChain API", version="1.0.0")

# Define chains
summarize_chain = (
    ChatPromptTemplate.from_template("Summarize in 3 sentences: {text}")
    | ChatOpenAI(model="gpt-4o-mini", temperature=0)
    | StrOutputParser()
)

qa_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "Answer based on the given context only."),
        ("human", "Context: {context}\n\nQuestion: {question}"),
    ])
    | ChatOpenAI(model="gpt-4o-mini")
    | StrOutputParser()
)

# Auto-generates /invoke, /batch, /stream, /input_schema, /output_schema
add_routes(app, summarize_chain, path="/summarize")
add_routes(app, qa_chain, path="/qa")

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Option B: Express API (Node.js/TypeScript)

```typescript
// server.ts
import express from "express";
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import "dotenv/config";

const app = express();
app.use(express.json());

const model = new ChatOpenAI({ model: "gpt-4o-mini" });
const summarizeChain = ChatPromptTemplate.fromTemplate("Summarize: {text}")
  .pipe(model)
  .pipe(new StringOutputParser());

app.post("/api/summarize", async (req, res) => {
  try {
    const result = await summarizeChain.invoke({ text: req.body.text });
    res.json({ result });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Streaming endpoint
app.post("/api/summarize/stream", async (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");

  const stream = await summarizeChain.stream({ text: req.body.text });
  for await (const chunk of stream) {
    res.write(`data: ${JSON.stringify({ chunk })}\n\n`);
  }
  res.write("data: [DONE]\n\n");
  res.end();
});

app.get("/health", (_req, res) => res.json({ status: "healthy" }));

app.listen(8000, () => console.log("Server running on :8000"));
```

## Dockerfile

```dockerfile
# Multi-stage build for Node.js
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./

ENV NODE_ENV=production
ENV LANGSMITH_TRACING=true

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["node", "dist/server.js"]
```

## Docker Compose

```yaml
version: "3.8"
services:
  langchain-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - LANGSMITH_TRACING=true
      - LANGSMITH_PROJECT=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
```

## Cloud Run Deployment

```bash
# Build and deploy to Cloud Run
gcloud run deploy langchain-api \
  --source . \
  --region us-central1 \
  --set-secrets=OPENAI_API_KEY=openai-key:latest \
  --set-secrets=LANGSMITH_API_KEY=langsmith-key:latest \
  --set-env-vars="LANGSMITH_TRACING=true,LANGSMITH_PROJECT=production" \
  --min-instances=1 \
  --max-instances=10 \
  --memory=1Gi \
  --timeout=60s \
  --port=8000
```

## Production Requirements

```
# requirements.txt (Python)
langchain>=0.3.0
langchain-openai>=0.2.0
langserve>=0.3.0
langsmith>=0.1.0
uvicorn>=0.30.0
fastapi>=0.115.0
gunicorn>=22.0.0
```

```json
// package.json dependencies (Node.js)
{
  "@langchain/core": "^0.3.0",
  "@langchain/openai": "^0.3.0",
  "langchain": "^0.3.0",
  "express": "^4.21.0",
  "dotenv": "^16.4.0"
}
```

## Health Check with LangSmith Verification

```typescript
app.get("/health", async (_req, res) => {
  const checks: Record<string, string> = { server: "ok" };

  try {
    await model.invoke("ping");
    checks.llm = "ok";
  } catch (e: any) {
    checks.llm = `error: ${e.message}`;
  }

  const allOk = Object.values(checks).every((v) => v === "ok");
  res.status(allOk ? 200 : 503).json({ status: allOk ? "healthy" : "degraded", checks });
});
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Cold start slow | Heavy imports | Use `--min-instances=1` or preload |
| Memory exceeded | Large context window | Increase container memory, use streaming |
| LangSmith timeout | Network issue | Set `LANGCHAIN_CALLBACKS_BACKGROUND=true` |
| Import errors in container | Missing deps | Pin exact versions in requirements/package.json |

## Resources

- [LangServe Docs](https://python.langchain.com/docs/langserve)
- [LangSmith Production](https://docs.smith.langchain.com/)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

## Next Steps

For multi-environment setup, see `langchain-multi-env-setup`.
