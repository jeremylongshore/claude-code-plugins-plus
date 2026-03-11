---
name: langchain-performance-tuning
description: |
  Optimize LangChain application performance and latency.
  Use when reducing response times, optimizing throughput,
  or improving the efficiency of LangChain pipelines.
  Trigger with phrases like "langchain performance", "langchain optimization",
  "langchain latency", "langchain slow", "speed up langchain".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Performance Tuning

## Overview
Optimize LangChain applications for lower latency, higher throughput, and efficient resource utilization.

## Prerequisites
- Working LangChain application
- Performance baseline measurements
- Profiling tools available

## Instructions

### Step 1: Measure Baseline Performance
```python
import time
from functools import wraps
from typing import Callable
import statistics

def benchmark(func: Callable, iterations: int = 10):
    """Benchmark a function's performance."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "min": min(times),
        "max": max(times),
    }

# Usage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

def test_call():
    llm.invoke("Hello!")

results = benchmark(test_call, iterations=5)
print(f"Mean latency: {results['mean']:.3f}s")
```

### Step 2: Enable Response Caching
```python
from langchain_core.globals import set_llm_cache
from langchain_community.cache import InMemoryCache, SQLiteCache, RedisCache

# Option 1: In-memory cache (single process)
set_llm_cache(InMemoryCache())

# Option 2: SQLite cache (persistent, single node)
set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))

# Option 3: Redis cache (distributed, production)
import redis
redis_client = redis.Redis.from_url("redis://localhost:6379")  # 6379: Redis port
set_llm_cache(RedisCache(redis_client))

# Cache hit = ~0ms latency vs ~500-2000ms for API call
```

### Step 3: Optimize Batch Processing
```python
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_template("{input}")
chain = prompt | llm

# Sequential (slow)
def process_sequential(inputs: list) -> list:
    return [chain.invoke({"input": inp}) for inp in inputs]

# Batch (faster - automatic batching)
def process_batch(inputs: list) -> list:
    batch_inputs = [{"input": inp} for inp in inputs]
    return chain.batch(batch_inputs, config={"max_concurrency": 10})

# Async (fastest - true parallelism)
async def process_async(inputs: list) -> list:
    batch_inputs = [{"input": inp} for inp in inputs]
    return await chain.abatch(batch_inputs, config={"max_concurrency": 20})

# Benchmark: 10 items
# Sequential: ~10s (1s each)
# Batch: ~2s (parallel API calls)
# Async: ~1.5s (optimal parallelism)
```

### Step 4: Use Streaming for Perceived Performance
```python
from langchain_openai import ChatOpenAI

# Non-streaming: User waits for full response
llm = ChatOpenAI(model="gpt-4o-mini")
response = llm.invoke("Tell me a story")  # Wait 2-3 seconds

# Streaming: First token in ~200ms
llm_stream = ChatOpenAI(model="gpt-4o-mini", streaming=True)
for chunk in llm_stream.stream("Tell me a story"):
    print(chunk.content, end="", flush=True)
```

### Step 5: Optimize Prompt Length
```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Count tokens in text."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def optimize_prompt(prompt: str, max_tokens: int = 1000) -> str:  # 1 second in ms
    """Truncate prompt to fit token limit."""
    encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    tokens = encoding.encode(prompt)
    if len(tokens) <= max_tokens:
        return prompt
    return encoding.decode(tokens[:max_tokens])

# Example: Long context optimization
system_prompt = "You are a helpful assistant."  # ~5 tokens
user_context = "Here is the document: " + long_document  # Could be 10000+ tokens

# Optimize by summarizing or chunking context
```

### Step 6: Connection Pooling
```python
import httpx
from langchain_openai import ChatOpenAI

# Configure connection pooling for high throughput
transport = httpx.HTTPTransport(
    retries=3,
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20
    )
)

# Use shared client across requests
http_client = httpx.Client(transport=transport, timeout=30.0)

# Note: OpenAI SDK handles this internally, but for custom integrations:
llm = ChatOpenAI(
    model="gpt-4o-mini",
    http_client=http_client  # Reuse connections
)
```

### Step 7: Model Selection Optimization
```python
# Match model to task complexity

# Fast + Cheap: Simple tasks
llm_fast = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Powerful + Slower: Complex reasoning
llm_powerful = ChatOpenAI(model="gpt-4o", temperature=0)

# Router pattern: Choose model based on task
from langchain_core.runnables import RunnableBranch

def classify_complexity(input_dict: dict) -> str:
    """Classify input complexity."""
    text = input_dict.get("input", "")
    # Simple heuristic - replace with classifier
    return "complex" if len(text) > 500 else "simple"  # HTTP 500 Internal Server Error

router = RunnableBranch(
    (lambda x: classify_complexity(x) == "simple", prompt | llm_fast),
    prompt | llm_powerful  # Default to powerful
)
```

## Performance Metrics
| Optimization | Latency Improvement | Cost Impact |
|--------------|---------------------|-------------|
| Caching | 90-99% on cache hit | Major reduction |
| Batching | 50-80% for bulk | Neutral |
| Streaming | Perceived 80%+ | Neutral |
| Shorter prompts | 10-30% | Cost reduction |
| Connection pooling | 5-10% | Neutral |
| Model routing | 20-50% | Cost reduction |

## Output
- Performance benchmarking setup
- Caching implementation
- Optimized batch processing
- Streaming for perceived performance

## Resources
- [LangChain Caching](https://python.langchain.com/docs/how_to/llm_caching/)
- [OpenAI Latency Guide](https://platform.openai.com/docs/guides/latency-optimization)
- [tiktoken](https://github.com/openai/tiktoken)

## Next Steps
Use `langchain-cost-tuning` to optimize API costs alongside performance.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with CI/CD |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply langchain performance tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize langchain performance tuning for production environments with multiple constraints and team-specific requirements.