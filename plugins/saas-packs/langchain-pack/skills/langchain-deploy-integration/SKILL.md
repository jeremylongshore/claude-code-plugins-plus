---
name: langchain-deploy-integration
description: |
  Deploy LangChain integrations to production environments.
  Use when deploying to cloud platforms, configuring containers,
  or setting up production infrastructure for LangChain apps.
  Trigger with phrases like "deploy langchain", "langchain production deploy",
  "langchain cloud run", "langchain docker", "langchain kubernetes".
allowed-tools: Read, Write, Edit, Bash(docker:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# LangChain Deploy Integration

## Overview
Deploy LangChain applications to production using LangServe, Docker, and cloud platforms. Covers containerization of chains and agents, LangServe API deployment, and integration with LangSmith for production observability.

## Prerequisites
- LangChain application with chains/agents defined
- Docker installed for containerization
- LangSmith API key for production tracing
- Platform CLI (gcloud, aws, or docker compose)

## Instructions

### Step 1: LangServe API Setup
```python
# serve.py
from fastapi import FastAPI
from langserve import add_routes
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

app = FastAPI(title="LangChain API")

# Define your chain
prompt = ChatPromptTemplate.from_template("Answer: {question}")
chain = prompt | ChatOpenAI(model="gpt-4o-mini")

# Add LangServe routes
add_routes(app, chain, path="/chat")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 2: Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV LANGCHAIN_TRACING_V2=true
ENV LANGCHAIN_PROJECT=production

EXPOSE 8000
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 3: Docker Compose for Development
```yaml
version: "3.8"
services:
  langchain-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - LANGCHAIN_TRACING_V2=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
```

### Step 4: Cloud Run Deployment
```bash
gcloud run deploy langchain-api \
  --source . \
  --region us-central1 \
  --set-secrets=OPENAI_API_KEY=openai-key:latest \
  --set-secrets=LANGCHAIN_API_KEY=langsmith-key:latest \
  --set-env-vars=LANGCHAIN_TRACING_V2=true \
  --min-instances=1 \
  --memory=1Gi
```

### Step 5: Health Check with LangSmith
```python
from langsmith import Client

async def health_check():
    try:
        client = Client()
        # Verify LangSmith connection
        client.list_projects(limit=1)
        return {"status": "healthy", "tracing": "enabled"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Import errors | Missing dependencies | Pin versions in requirements.txt |
| LangSmith timeout | Network issue | Set `LANGCHAIN_TRACING_V2=false` as fallback |
| Memory exceeded | Large context | Increase container memory, use streaming |
| Cold start slow | Heavy imports | Use gunicorn with preload |

## Examples

### Production Requirements
```text
langchain>=0.3.0
langchain-openai>=0.2.0
langserve>=0.3.0
langsmith>=0.1.0
uvicorn>=0.30.0
fastapi>=0.115.0
```

## Resources
- [LangServe Documentation](https://python.langchain.com/docs/langserve)
- [LangSmith](https://docs.smith.langchain.com)
- [LangChain Deployment](https://python.langchain.com/docs/guides/deployment)

## Next Steps
For multi-environment setup, see `langchain-multi-env-setup`.
