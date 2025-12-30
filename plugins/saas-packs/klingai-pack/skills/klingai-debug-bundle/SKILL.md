---
name: klingai-debug-bundle
description: |
  Set up comprehensive logging and debugging for Kling AI. Use when investigating issues or
  monitoring requests. Trigger with phrases like 'klingai debug', 'kling ai logging',
  'trace klingai', 'monitor klingai requests'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Debug Bundle

## Overview

This skill shows how to implement request/response logging, timing metrics, and debugging utilities for Kling AI integrations to quickly identify and resolve issues.

## Prerequisites

- Kling AI integration
- Python 3.8+ or Node.js 18+
- Logging infrastructure (optional but recommended)

## Instructions

Follow these steps to set up debugging:

1. **Configure Logging**: Set up structured logging
2. **Add Request Tracing**: Track all API requests
3. **Implement Timing**: Measure performance metrics
4. **Create Debug Utilities**: Build diagnostic tools
5. **Set Up Alerts**: Configure error notifications

## Logging Setup

```python
import logging
import json
from datetime import datetime
from typing import Any
import sys

# Configure structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def setup_logging(level=logging.INFO):
    """Configure logging for Kling AI debugging."""
    logger = logging.getLogger("klingai")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger

logger = setup_logging()
```

## Request Tracing

```python
import time
import uuid
from functools import wraps
from dataclasses import dataclass, asdict
from typing import Optional
import requests

@dataclass
class RequestTrace:
    trace_id: str
    method: str
    url: str
    request_body: Optional[dict]
    response_status: int
    response_body: Optional[dict]
    duration_ms: float
    timestamp: str
    error: Optional[str] = None

class TracedKlingAIClient:
    """Kling AI client with full request tracing."""

    def __init__(self, api_key: str, base_url: str = "https://api.klingai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.traces: list[RequestTrace] = []
        self.logger = logging.getLogger("klingai.trace")

    def _traced_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> dict:
        """Make request with full tracing."""
        trace_id = str(uuid.uuid4())[:8]
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        # Log request
        self.logger.info(f"[{trace_id}] {method} {endpoint}", extra={
            "trace_id": trace_id,
            "method": method,
            "endpoint": endpoint,
            "body": kwargs.get("json")
        })

        try:
            response = requests.request(
                method,
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "X-Trace-ID": trace_id
                },
                **kwargs
            )
            duration = (time.time() - start_time) * 1000

            # Create trace record
            trace = RequestTrace(
                trace_id=trace_id,
                method=method,
                url=url,
                request_body=kwargs.get("json"),
                response_status=response.status_code,
                response_body=response.json() if response.text else None,
                duration_ms=duration,
                timestamp=datetime.utcnow().isoformat()
            )
            self.traces.append(trace)

            # Log response
            self.logger.info(f"[{trace_id}] Response {response.status_code}", extra={
                "trace_id": trace_id,
                "status": response.status_code,
                "duration_ms": duration
            })

            response.raise_for_status()
            return response.json()

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            trace = RequestTrace(
                trace_id=trace_id,
                method=method,
                url=url,
                request_body=kwargs.get("json"),
                response_status=getattr(e, "response", {}).status_code if hasattr(e, "response") else 0,
                response_body=None,
                duration_ms=duration,
                timestamp=datetime.utcnow().isoformat(),
                error=str(e)
            )
            self.traces.append(trace)

            self.logger.error(f"[{trace_id}] Error: {e}", extra={
                "trace_id": trace_id,
                "error": str(e),
                "duration_ms": duration
            })
            raise

    def get_traces(self, limit: int = 100) -> list[dict]:
        """Get recent traces."""
        return [asdict(t) for t in self.traces[-limit:]]

    def export_traces(self, filepath: str):
        """Export traces to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.get_traces(), f, indent=2)
```

## Performance Metrics

```python
from dataclasses import dataclass, field
from statistics import mean, median, stdev
from collections import defaultdict

@dataclass
class PerformanceMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration_ms: float = 0
    durations: list = field(default_factory=list)
    errors_by_type: dict = field(default_factory=lambda: defaultdict(int))
    requests_by_endpoint: dict = field(default_factory=lambda: defaultdict(int))

    def record_request(self, duration_ms: float, endpoint: str, success: bool, error: str = None):
        self.total_requests += 1
        self.total_duration_ms += duration_ms
        self.durations.append(duration_ms)
        self.requests_by_endpoint[endpoint] += 1

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if error:
                self.errors_by_type[error] += 1

    def get_stats(self) -> dict:
        if not self.durations:
            return {}

        return {
            "total_requests": self.total_requests,
            "success_rate": self.successful_requests / self.total_requests * 100,
            "avg_duration_ms": mean(self.durations),
            "median_duration_ms": median(self.durations),
            "p95_duration_ms": sorted(self.durations)[int(len(self.durations) * 0.95)],
            "min_duration_ms": min(self.durations),
            "max_duration_ms": max(self.durations),
            "stddev_duration_ms": stdev(self.durations) if len(self.durations) > 1 else 0,
            "errors_by_type": dict(self.errors_by_type),
            "requests_by_endpoint": dict(self.requests_by_endpoint)
        }

metrics = PerformanceMetrics()
```

## Debug Utilities

```python
def create_debug_report(client: TracedKlingAIClient, metrics: PerformanceMetrics) -> dict:
    """Generate comprehensive debug report."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "performance": metrics.get_stats(),
        "recent_traces": client.get_traces(limit=10),
        "configuration": {
            "base_url": client.base_url,
            "api_key_set": bool(client.api_key),
            "api_key_prefix": client.api_key[:10] + "..." if client.api_key else None
        }
    }

def diagnose_issue(trace: RequestTrace) -> dict:
    """Analyze a trace for common issues."""
    issues = []
    suggestions = []

    # Check duration
    if trace.duration_ms > 30000:
        issues.append("Request took too long (>30s)")
        suggestions.append("Consider shorter duration or simpler prompt")

    # Check status
    if trace.response_status == 401:
        issues.append("Authentication failed")
        suggestions.append("Verify API key is valid and properly formatted")
    elif trace.response_status == 429:
        issues.append("Rate limit exceeded")
        suggestions.append("Implement exponential backoff")
    elif trace.response_status >= 500:
        issues.append("Server error")
        suggestions.append("Retry with backoff, check status page")

    # Check error
    if trace.error:
        if "timeout" in trace.error.lower():
            issues.append("Request timed out")
            suggestions.append("Increase timeout or reduce complexity")

    return {
        "trace_id": trace.trace_id,
        "issues": issues,
        "suggestions": suggestions,
        "severity": "high" if trace.response_status >= 500 else "medium" if issues else "low"
    }
```

## Debug Mode Wrapper

```python
import os

DEBUG_MODE = os.environ.get("KLINGAI_DEBUG", "false").lower() == "true"

def debug_wrapper(func):
    """Wrapper to add debug output to any function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if DEBUG_MODE:
            print(f"[DEBUG] Calling {func.__name__}")
            print(f"[DEBUG] Args: {args}")
            print(f"[DEBUG] Kwargs: {kwargs}")

        start = time.time()
        try:
            result = func(*args, **kwargs)
            if DEBUG_MODE:
                duration = (time.time() - start) * 1000
                print(f"[DEBUG] {func.__name__} completed in {duration:.2f}ms")
                print(f"[DEBUG] Result: {result}")
            return result
        except Exception as e:
            if DEBUG_MODE:
                print(f"[DEBUG] {func.__name__} failed: {e}")
            raise
    return wrapper
```

## Output

Successful execution produces:
- Structured logging output
- Request traces with timing
- Performance metrics dashboard
- Debug reports for troubleshooting

## Error Handling

Common errors and solutions:
1. **Missing Logs**: Ensure logging is configured before client initialization
2. **Memory Growth**: Limit trace history size
3. **Performance Impact**: Disable debug mode in production

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Python Logging](https://docs.python.org/3/library/logging.html)
- [Structured Logging Best Practices](https://www.structlog.org/)
- [OpenTelemetry](https://opentelemetry.io/)
