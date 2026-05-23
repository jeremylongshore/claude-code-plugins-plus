# Client Layer Implementation

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
