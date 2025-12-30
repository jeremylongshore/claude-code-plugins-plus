---
name: klingai-sdk-patterns
description: |
  Implement common SDK patterns for Kling AI integration. Use when building production applications
  with Kling AI. Trigger with phrases like 'klingai sdk', 'kling ai client', 'klingai patterns',
  'kling ai best practices'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI SDK Patterns

## Overview

This skill covers proven SDK patterns including client initialization, error handling, retry logic, async job management, and configuration management for robust Kling AI integrations.

## Prerequisites

- Kling AI API key configured
- Python 3.8+ or Node.js 18+
- Understanding of async programming concepts

## Instructions

Follow these steps to implement SDK patterns:

1. **Create Client Wrapper**: Build a reusable client class
2. **Implement Error Handling**: Add robust error handling
3. **Add Retry Logic**: Handle transient failures
4. **Manage Async Jobs**: Track generation jobs properly
5. **Configure Timeouts**: Set appropriate timeout values

## Python Client Pattern

```python
import os
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class VideoResult:
    job_id: str
    status: JobStatus
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    error: Optional[str] = None
    duration: Optional[int] = None
    metadata: Optional[Dict] = None

class KlingAIClient:
    """Production-ready Kling AI client."""

    DEFAULT_BASE_URL = "https://api.klingai.com/v1"
    DEFAULT_TIMEOUT = 30
    DEFAULT_POLL_INTERVAL = 5
    DEFAULT_MAX_WAIT = 600

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.environ.get("KLINGAI_API_KEY")
        if not self.api_key:
            raise ValueError("KLINGAI_API_KEY required")

        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout

        # Configure session with retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        model: str = "kling-v1.5",
        aspect_ratio: str = "16:9",
        **kwargs
    ) -> str:
        """Submit text-to-video generation job."""
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            **kwargs
        }
        result = self._request("POST", "/videos/text2video", json=payload)
        return result["job_id"]

    def image_to_video(
        self,
        image_url: str,
        motion_prompt: str,
        duration: int = 5,
        model: str = "kling-v1.5",
        **kwargs
    ) -> str:
        """Submit image-to-video generation job."""
        payload = {
            "model": model,
            "image_url": image_url,
            "motion_prompt": motion_prompt,
            "duration": duration,
            **kwargs
        }
        result = self._request("POST", "/videos/image2video", json=payload)
        return result["job_id"]

    def get_job_status(self, job_id: str) -> VideoResult:
        """Get current status of a generation job."""
        result = self._request("GET", f"/videos/{job_id}")
        return VideoResult(
            job_id=job_id,
            status=JobStatus(result["status"]),
            video_url=result.get("video_url"),
            thumbnail_url=result.get("thumbnail_url"),
            error=result.get("error"),
            duration=result.get("duration"),
            metadata=result
        )

    def wait_for_completion(
        self,
        job_id: str,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        max_wait: int = DEFAULT_MAX_WAIT,
        callback: Optional[callable] = None
    ) -> VideoResult:
        """Wait for job completion with polling."""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            result = self.get_job_status(job_id)

            if callback:
                callback(result)

            if result.status == JobStatus.COMPLETED:
                return result
            elif result.status == JobStatus.FAILED:
                raise Exception(f"Generation failed: {result.error}")

            time.sleep(poll_interval)

        raise TimeoutError(f"Job {job_id} timed out after {max_wait}s")

    def generate_video(
        self,
        prompt: str,
        wait: bool = True,
        **kwargs
    ) -> VideoResult:
        """High-level method: generate video and optionally wait."""
        job_id = self.text_to_video(prompt, **kwargs)

        if wait:
            return self.wait_for_completion(job_id)

        return VideoResult(job_id=job_id, status=JobStatus.PENDING)

# Usage
client = KlingAIClient()
result = client.generate_video(
    prompt="A cat playing piano in a jazz club",
    duration=10,
    model="kling-v1.5"
)
print(f"Video URL: {result.video_url}")
```

## TypeScript Client Pattern

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';

enum JobStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

interface VideoResult {
  jobId: string;
  status: JobStatus;
  videoUrl?: string;
  thumbnailUrl?: string;
  error?: string;
  duration?: number;
  metadata?: Record<string, any>;
}

interface KlingAIConfig {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
}

class KlingAIClient {
  private client: AxiosInstance;
  private static DEFAULT_BASE_URL = 'https://api.klingai.com/v1';
  private static DEFAULT_TIMEOUT = 30000;
  private static DEFAULT_POLL_INTERVAL = 5000;
  private static DEFAULT_MAX_WAIT = 600000;

  constructor(config: KlingAIConfig = {}) {
    const apiKey = config.apiKey || process.env.KLINGAI_API_KEY;
    if (!apiKey) {
      throw new Error('KLINGAI_API_KEY required');
    }

    this.client = axios.create({
      baseURL: config.baseUrl || KlingAIClient.DEFAULT_BASE_URL,
      timeout: config.timeout || KlingAIClient.DEFAULT_TIMEOUT,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    // Add retry interceptor
    this.client.interceptors.response.use(
      response => response,
      async (error: AxiosError) => {
        const config = error.config as any;
        config.retryCount = config.retryCount || 0;

        if (config.retryCount < (config.maxRetries || 3) &&
            [429, 500, 502, 503, 504].includes(error.response?.status || 0)) {
          config.retryCount++;
          await this.delay(Math.pow(2, config.retryCount) * 1000);
          return this.client.request(config);
        }

        throw error;
      }
    );
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async textToVideo(params: {
    prompt: string;
    duration?: number;
    model?: string;
    aspectRatio?: string;
  }): Promise<string> {
    const response = await this.client.post('/videos/text2video', {
      model: params.model || 'kling-v1.5',
      prompt: params.prompt,
      duration: params.duration || 5,
      aspect_ratio: params.aspectRatio || '16:9'
    });
    return response.data.job_id;
  }

  async getJobStatus(jobId: string): Promise<VideoResult> {
    const response = await this.client.get(`/videos/${jobId}`);
    return {
      jobId,
      status: response.data.status as JobStatus,
      videoUrl: response.data.video_url,
      thumbnailUrl: response.data.thumbnail_url,
      error: response.data.error,
      duration: response.data.duration,
      metadata: response.data
    };
  }

  async waitForCompletion(
    jobId: string,
    options: { pollInterval?: number; maxWait?: number; callback?: (result: VideoResult) => void } = {}
  ): Promise<VideoResult> {
    const pollInterval = options.pollInterval || KlingAIClient.DEFAULT_POLL_INTERVAL;
    const maxWait = options.maxWait || KlingAIClient.DEFAULT_MAX_WAIT;
    const startTime = Date.now();

    while (Date.now() - startTime < maxWait) {
      const result = await this.getJobStatus(jobId);

      if (options.callback) {
        options.callback(result);
      }

      if (result.status === JobStatus.COMPLETED) {
        return result;
      } else if (result.status === JobStatus.FAILED) {
        throw new Error(`Generation failed: ${result.error}`);
      }

      await this.delay(pollInterval);
    }

    throw new Error(`Job ${jobId} timed out after ${maxWait}ms`);
  }

  async generateVideo(params: {
    prompt: string;
    wait?: boolean;
    duration?: number;
    model?: string;
  }): Promise<VideoResult> {
    const jobId = await this.textToVideo(params);

    if (params.wait !== false) {
      return this.waitForCompletion(jobId);
    }

    return { jobId, status: JobStatus.PENDING };
  }
}

// Usage
const client = new KlingAIClient();
const result = await client.generateVideo({
  prompt: 'A cat playing piano in a jazz club',
  duration: 10
});
console.log(`Video URL: ${result.videoUrl}`);
```

## Error Handling Pattern

```python
from enum import Enum

class KlingAIError(Exception):
    """Base exception for Kling AI errors."""
    pass

class AuthenticationError(KlingAIError):
    """Invalid or missing API key."""
    pass

class RateLimitError(KlingAIError):
    """Rate limit exceeded."""
    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after}s")

class ContentPolicyError(KlingAIError):
    """Content violates usage policy."""
    pass

class GenerationError(KlingAIError):
    """Video generation failed."""
    pass

def handle_api_error(response: requests.Response):
    """Convert HTTP errors to specific exceptions."""
    if response.status_code == 401:
        raise AuthenticationError("Invalid API key")
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        raise RateLimitError(retry_after)
    elif response.status_code == 400:
        error = response.json().get("error", {})
        if "content_policy" in error.get("code", ""):
            raise ContentPolicyError(error.get("message"))
        raise KlingAIError(error.get("message", "Bad request"))
    elif response.status_code >= 500:
        raise KlingAIError(f"Server error: {response.status_code}")
```

## Output

Successful execution produces:
- Robust, production-ready client code
- Proper error handling and retry logic
- Async job management patterns

## Error Handling

Common errors and solutions:
1. **Connection Timeout**: Increase timeout or check network
2. **Rate Limit**: Implement backoff and retry
3. **Authentication**: Verify API key configuration
4. **Job Timeout**: Increase max wait time for long videos

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI API Reference](https://docs.klingai.com/api)
- [Error Codes](https://docs.klingai.com/errors)
- [Rate Limits](https://docs.klingai.com/rate-limits)
