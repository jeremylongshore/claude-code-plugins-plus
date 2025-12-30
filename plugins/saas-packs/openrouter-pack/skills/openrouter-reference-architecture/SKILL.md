---
name: openrouter-reference-architecture
description: |
  Production reference architecture for OpenRouter deployments. Use when designing or reviewing system architecture. Trigger with phrases like 'openrouter architecture', 'openrouter design', 'production openrouter', 'openrouter infrastructure'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Reference Architecture

## Overview

This skill provides a complete reference architecture for production OpenRouter deployments including infrastructure, monitoring, and operational patterns.

## Prerequisites

- Understanding of cloud infrastructure
- Production deployment requirements defined

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill provides a complete reference architecture for production OpenRouter deployments including infrastructure, monitoring, and operational patterns.

## Prerequisites

- Understanding of cloud infrastructure
- Production deployment requirements defined

## Basic Production Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web App    │  │   API        │  │   Workers    │          │
│  │   (React)    │  │   (FastAPI)  │  │   (Celery)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                     │
│  ┌────────────────────────┴─────────────────────────────┐      │
│  │                 OpenRouter Client Layer               │      │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │      │
│  │  │ Router  │  │ Fallback│  │  Cache  │  │ Monitor │ │      │
│  │  │ (Model) │  │ Manager │  │  Layer  │  │  Layer  │ │      │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘ │      │
│  │       └────────────┴────────────┴────────────┘       │      │
│  └──────────────────────────┬───────────────────────────┘      │
│                             │                                   │
├─────────────────────────────┴───────────────────────────────────┤
│                        OpenRouter API                            │
│                  https://openrouter.ai/api/v1                    │
└─────────────────────────────────────────────────────────────────┘
```

## Client Layer Implementation

### Production OpenRouter Service
```python
from openai import OpenAI, AsyncOpenAI
import os
import time
import logging
from dataclasses import dataclass
from typing import Optional, List
from functools import lru_cache
import redis
import hashlib
import json

@dataclass
class OpenRouterConfig:
    api_key: str
    default_model: str = "anthropic/claude-3.5-sonnet"
    fallback_models: List[str] = None
    timeout: float = 60.0
    max_retries: int = 3
    cache_ttl: int = 3600
    http_referer: str = ""
    x_title: str = ""

    def __post_init__(self):
        if self.fallback_models is None:
            self.fallback_models = [
                "openai/gpt-4-turbo",
                "meta-llama/llama-3.1-70b-instruct"
            ]

class OpenRouterService:
    """Production-ready OpenRouter service."""

    def __init__(self, config: OpenRouterConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Sync client
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=config.max_retries,
            default_headers={
                "HTTP-Referer": config.http_referer,
                "X-Title": config.x_title,
            }
        )

        # Async client
        self.async_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=config.max_retries,
            default_headers={
                "HTTP-Referer": config.http_referer,
                "X-Title": config.x_title,
            }
        )

        # Redis cache (optional)
        self.redis = None
        if os.environ.get("REDIS_URL"):
            self.redis = redis.from_url(os.environ["REDIS_URL"])

        # Metrics
        self.request_count = 0
        self.error_count = 0

    def _cache_key(self, model: str, messages: list) -> str:
        content = json.dumps({"model": model, "messages": messages}, sort_keys=True)
        return f"openrouter:{hashlib.sha256(content.encode()).hexdigest()}"

    def _get_cached(self, model: str, messages: list) -> Optional[str]:
        if not self.redis:
            return None
        try:
            key = self._cache_key(model, messages)
            value = self.redis.get(key)
            return value.decode() if value else None
        except Exception as e:
            self.logger.warning(f"Cache get failed: {e}")
            return None

    def _set_cached(self, model: str, messages: list, value: str):
        if not self.redis:
            return
        try:
            key = self._cache_key(model, messages)
            self.redis.setex(key, self.config.cache_ttl, value)
        except Exception as e:
            self.logger.warning(f"Cache set failed: {e}")

    def chat(
        self,
        prompt: str,
        model: str = None,
        system: str = None,
        use_cache: bool = True,
        **kwargs
    ) -> str:
        """Synchronous chat with fallback and caching."""
        model = model or self.config.default_model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Check cache
        if use_cache:
            cached = self._get_cached(model, messages)
            if cached:
                self.logger.debug("Cache hit")
                return cached

        # Try primary model
        models_to_try = [model] + self.config.fallback_models

        for try_model in models_to_try:
            try:
                self.request_count += 1
                response = self.client.chat.completions.create(
                    model=try_model,
                    messages=messages,
                    **kwargs
                )
                content = response.choices[0].message.content

                # Cache result
                if use_cache:
                    self._set_cached(try_model, messages, content)

                return content

            except Exception as e:
                self.error_count += 1
                self.logger.warning(f"Model {try_model} failed: {e}")
                if "unavailable" in str(e).lower():
                    continue
                raise

        raise Exception("All models failed")

    async def chat_async(
        self,
        prompt: str,
        model: str = None,
        system: str = None,
        **kwargs
    ) -> str:
        """Async chat with fallback."""
        model = model or self.config.default_model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        models_to_try = [model] + self.config.fallback_models

        for try_model in models_to_try:
            try:
                response = await self.async_client.chat.completions.create(
                    model=try_model,
                    messages=messages,
                    **kwargs
                )
                return response.choices[0].message.content

            except Exception as e:
                self.logger.warning(f"Model {try_model} failed: {e}")
                continue

        raise Exception("All models failed")

    def stream(self, prompt: str, model: str = None, **kwargs):
        """Streaming response."""
        model = model or self.config.default_model
        messages = [{"role": "user", "content": prompt}]

        stream = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def metrics(self) -> dict:
        """Return service metrics."""
        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
        }
```

## Microservice Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Load Balancer                              │
│                         (nginx / ALB)                                │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
┌──────┴──────┐      ┌──────┴──────┐      ┌──────┴──────┐
│   API GW    │      │   API GW    │      │   API GW    │
│  (replica)  │      │  (replica)  │      │  (replica)  │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    ┌───────┴───────┐
                    │ Message Queue │
                    │   (Redis)     │
                    └───────┬───────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
┌──────┴──────┐      ┌──────┴──────┐      ┌──────┴──────┐
│   Worker    │      │   Worker    │      │   Worker    │
│ (OpenRouter)│      │ (OpenRouter)│      │ (OpenRouter)│
└─────────────┘      └─────────────┘      └─────────────┘
```

### Worker Service
```python
# worker.py
from celery import Celery
from openrouter_service import OpenRouterService, OpenRouterConfig

app = Celery('llm_worker', broker=os.environ["REDIS_URL"])

config = OpenRouterConfig(
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_model="anthropic/claude-3.5-sonnet"
)
service = OpenRouterService(config)

@app.task(bind=True, max_retries=3)
def process_llm_request(self, prompt: str, model: str = None, **kwargs):
    try:
        return service.chat(prompt, model=model, **kwargs)
    except Exception as e:
        self.retry(countdown=2 ** self.request.retries)

@app.task
def process_batch(prompts: list, model: str = None):
    results = []
    for prompt in prompts:
        try:
            result = service.chat(prompt, model=model)
            results.append({"prompt": prompt, "result": result, "success": True})
        except Exception as e:
            results.append({"prompt": prompt, "error": str(e), "success": False})
    return results
```

### API Gateway
```python
# api.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from worker import process_llm_request, process_batch

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str
    model: str = None
    async_mode: bool = False

class BatchRequest(BaseModel):
    prompts: list[str]
    model: str = None

@app.post("/chat")
async def chat(request: ChatRequest):
    if request.async_mode:
        # Async processing
        task = process_llm_request.delay(request.prompt, request.model)
        return {"task_id": task.id}
    else:
        # Sync processing
        result = process_llm_request(request.prompt, request.model)
        return {"result": result}

@app.post("/batch")
async def batch(request: BatchRequest):
    task = process_batch.delay(request.prompts, request.model)
    return {"task_id": task.id}

@app.get("/task/{task_id}")
async def get_task_result(task_id: str):
    result = AsyncResult(task_id)
    if result.ready():
        return {"status": "complete", "result": result.get()}
    return {"status": "pending"}
```

## Kubernetes Deployment

### Deployment Manifest
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openrouter-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: openrouter-service
  template:
    metadata:
      labels:
        app: openrouter-service
    spec:
      containers:
      - name: api
        image: your-registry/openrouter-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: openrouter-secrets
              key: api-key
        - name: REDIS_URL
          value: redis://redis-service:6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: openrouter-service
spec:
  selector:
    app: openrouter-service
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Horizontal Pod Autoscaler
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: openrouter-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: openrouter-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Monitoring Stack

### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
REQUEST_COUNT = Counter(
    'openrouter_requests_total',
    'Total requests to OpenRouter',
    ['model', 'status']
)

REQUEST_LATENCY = Histogram(
    'openrouter_request_latency_seconds',
    'Request latency in seconds',
    ['model']
)

TOKENS_USED = Counter(
    'openrouter_tokens_total',
    'Total tokens used',
    ['model', 'type']
)

ACTIVE_REQUESTS = Gauge(
    'openrouter_active_requests',
    'Currently active requests'
)

def instrumented_chat(service: OpenRouterService, prompt: str, model: str):
    ACTIVE_REQUESTS.inc()
    start = time.time()

    try:
        response = service.chat(prompt, model=model)
        REQUEST_COUNT.labels(model=model, status="success").inc()
        return response

    except Exception as e:
        REQUEST_COUNT.labels(model=model, status="error").inc()
        raise

    finally:
        latency = time.time() - start
        REQUEST_LATENCY.labels(model=model).observe(latency)
        ACTIVE_REQUESTS.dec()

# Start metrics server
start_http_server(9090)
```

### Grafana Dashboard JSON
```json
{
  "title": "OpenRouter Service",
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(openrouter_requests_total[5m])",
          "legendFormat": "{{model}} - {{status}}"
        }
      ]
    },
    {
      "title": "Latency P95",
      "type": "graph",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(openrouter_request_latency_seconds_bucket[5m]))",
          "legendFormat": "{{model}}"
        }
      ]
    },
    {
      "title": "Error Rate",
      "type": "singlestat",
      "targets": [
        {
          "expr": "sum(rate(openrouter_requests_total{status='error'}[5m])) / sum(rate(openrouter_requests_total[5m]))"
        }
      ]
    }
  ]
}
```

## Security Configuration

### Secrets Management
```python
# Using Google Cloud Secret Manager
from google.cloud import secretmanager

def get_secret(project_id: str, secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# Initialize with secrets
config = OpenRouterConfig(
    api_key=get_secret("my-project", "openrouter-api-key"),
    default_model="anthropic/claude-3.5-sonnet"
)
```

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
