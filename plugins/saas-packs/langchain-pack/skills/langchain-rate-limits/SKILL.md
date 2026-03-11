---
name: langchain-rate-limits
description: |
  Implement LangChain rate limiting and backoff strategies.
  Use when handling API quotas, implementing retry logic,
  or optimizing request throughput for LLM providers.
  Trigger with phrases like "langchain rate limit", "langchain throttling",
  "langchain backoff", "langchain retry", "API quota".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Rate Limits

## Overview
Implement robust rate limiting and retry strategies for LangChain applications to handle API quotas gracefully.

## Prerequisites
- LangChain installed with LLM provider
- Understanding of provider rate limits
- tenacity package for advanced retry logic

## Instructions

### Step 1: Understand Provider Limits
```python
# Common rate limits by provider:
RATE_LIMITS = {
    "openai": {
        "gpt-4o": {"rpm": 10000, "tpm": 800000},  # 800000: 10000: 10 seconds in ms
        "gpt-4o-mini": {"rpm": 10000, "tpm": 4000000},  # 4000000: 10 seconds in ms
    },
    "anthropic": {
        "claude-3-5-sonnet": {"rpm": 4000, "tpm": 400000},  # 400000: 4000: dev server port
    },
    "google": {
        "gemini-1.5-pro": {"rpm": 360, "tpm": 4000000},  # 360 = configured value
    }
}
# rpm = requests per minute, tpm = tokens per minute
```

### Step 2: Built-in Retry Configuration
```python
from langchain_openai import ChatOpenAI

# LangChain has built-in retry with exponential backoff
llm = ChatOpenAI(
    model="gpt-4o-mini",
    max_retries=3,  # Number of retries
    request_timeout=30,  # Timeout per request
)
```

### Step 3: Advanced Retry with Tenacity
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from openai import RateLimitError, APIError

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((RateLimitError, APIError))
)
def call_with_retry(chain, input_data):
    """Call chain with exponential backoff."""
    return chain.invoke(input_data)

# Usage
result = call_with_retry(chain, {"input": "Hello"})
```

### Step 4: Rate Limiter Wrapper
```python
import asyncio
import time
from collections import deque
from threading import Lock

class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self.timestamps = deque()
        self.lock = Lock()

    def acquire(self):
        """Block until request can be made."""
        with self.lock:
            now = time.time()
            # Remove timestamps older than 1 minute
            while self.timestamps and now - self.timestamps[0] > 60:
                self.timestamps.popleft()

            if len(self.timestamps) >= self.rpm:
                sleep_time = 60 - (now - self.timestamps[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)

            self.timestamps.append(time.time())

# Usage with LangChain
rate_limiter = RateLimiter(requests_per_minute=100)

def rate_limited_call(chain, input_data):
    rate_limiter.acquire()
    return chain.invoke(input_data)
```

### Step 5: Async Rate Limiting
```python
import asyncio
from asyncio import Semaphore

class AsyncRateLimiter:
    """Async rate limiter with semaphore."""

    def __init__(self, max_concurrent: int = 10):
        self.semaphore = Semaphore(max_concurrent)

    async def call(self, chain, input_data):
        async with self.semaphore:
            return await chain.ainvoke(input_data)

# Batch processing with rate limiting
async def process_batch(chain, inputs: list, max_concurrent: int = 5):
    limiter = AsyncRateLimiter(max_concurrent)
    tasks = [limiter.call(chain, inp) for inp in inputs]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

## Output
- Configured retry logic with exponential backoff
- Rate limiter class for request throttling
- Async batch processing with concurrency control
- Graceful handling of rate limit errors

## Examples

### Handling Rate Limits in Production
```python
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

llm = ChatOpenAI(
    model="gpt-4o-mini",
    max_retries=5,
)

# Use batch with max_concurrency
inputs = [{"input": f"Query {i}"} for i in range(100)]

results = chain.batch(
    inputs,
    config=RunnableConfig(max_concurrency=10)  # Limit concurrent calls
)
```

### Fallback on Rate Limit
```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

primary = ChatOpenAI(model="gpt-4o-mini", max_retries=2)
fallback = ChatAnthropic(model="claude-3-5-sonnet-20241022")  # 20241022 = date/version stamp

# Automatically switch to fallback on rate limit
robust_llm = primary.with_fallbacks([fallback])
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| RateLimitError | Exceeded quota | Implement backoff, reduce concurrency |
| Timeout | Request too slow | Increase timeout, check network |
| 429 Too Many Requests | API throttled | Wait and retry with backoff |
| Quota Exceeded | Monthly limit hit | Upgrade plan or switch provider |

## Resources
- [OpenAI Rate Limits](https://platform.openai.com/docs/guides/rate-limits)
- [Anthropic Rate Limits](https://docs.anthropic.com/en/api/rate-limits)
- [tenacity Documentation](https://tenacity.readthedocs.io/)

## Next Steps
Proceed to `langchain-security-basics` for security best practices.