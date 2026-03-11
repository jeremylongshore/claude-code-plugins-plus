# Lindy Rate Limits - Implementation Guide

# Lindy Rate Limits

## Overview
Rate limit management for Lindy AI agent API. Lindy's agent execution model involves orchestrating multiple service calls per request, making rate limits apply at both the API level and the agent action level.

## Prerequisites
- Lindy API configured
- Understanding of agent execution costs
- Monitoring for action-level limits

## Lindy Rate Limits

| Resource | Limit | Window |
|----------|-------|--------|
| API Requests | 100/min | Per API key |
| Agent Triggers | 50/min | Per agent |
| Actions Per Agent | 200/hour | Per agent |
| Webhook Deliveries | 500/min | Per endpoint |

## Instructions

### Step 1: API-Level Rate Limiter

```python
import time

class LindyRateLimiter:
    def __init__(self, rpm: int = 100):
        self.rpm = rpm
        self.timestamps = []

    def wait(self):
        now = time.time()
        self.timestamps = [t for t in self.timestamps if now - t < 60]
        if len(self.timestamps) >= self.rpm:
            sleep_time = 60 - (now - self.timestamps[0])
            time.sleep(sleep_time + 0.1)
        self.timestamps.append(time.time())

limiter = LindyRateLimiter(rpm=100)

def call_lindy_api(endpoint: str, payload: dict):
    limiter.wait()
    response = requests.post(
        f"https://api.lindy.ai/v1/{endpoint}",
        json=payload, headers={"Authorization": f"Bearer {API_KEY}"}
    )
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 10))
        time.sleep(retry_after)
        return call_lindy_api(endpoint, payload)
    response.raise_for_status()
    return response.json()
```

### Step 2: Agent Action Budget

Track actions per agent to prevent hitting hourly limits.

```python
class AgentActionBudget:
    def __init__(self, hourly_limit: int = 200):
        self.limit = hourly_limit
        self.actions = {}  # agent_id -> [(timestamp, action)]

    def can_execute(self, agent_id: str) -> bool:
        now = time.time()
        history = self.actions.get(agent_id, [])
        recent = [t for t, _ in history if now - t < 3600]
        return len(recent) < self.limit

    def record(self, agent_id: str, action: str):
        if agent_id not in self.actions:
            self.actions[agent_id] = []
        self.actions[agent_id].append((time.time(), action))

    def remaining(self, agent_id: str) -> int:
        now = time.time()
        recent = [t for t, _ in self.actions.get(agent_id, []) if now - t < 3600]
        return max(0, self.limit - len(recent))

budget = AgentActionBudget()
```

### Step 3: Webhook Rate Management

```python
from collections import defaultdict

class WebhookRateTracker:
    def __init__(self, max_per_minute: int = 500):
        self.limit = max_per_minute
        self.counts = defaultdict(list)

    def should_process(self, endpoint: str) -> bool:
        now = time.time()
        self.counts[endpoint] = [t for t in self.counts[endpoint] if now - t < 60]
        if len(self.counts[endpoint]) >= self.limit:
            return False
        self.counts[endpoint].append(now)
        return True
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 API response | Exceeded 100 RPM | Rate limiter with backoff |
| Agent actions blocked | Exceeded 200 actions/hour | Track and budget agent actions |
| Webhook flood | External trigger storm | Rate limit webhook processing |
| Agent stalled | Hit action limit mid-workflow | Monitor remaining budget |

## Examples

### Status Dashboard
```python
status = {
    "api_rpm_used": len(limiter.timestamps),
    "agents": {
        agent_id: {"actions_remaining": budget.remaining(agent_id)}
        for agent_id in budget.actions
    }
}
```

## Resources
- [Lindy API Docs](https://docs.lindy.ai)
