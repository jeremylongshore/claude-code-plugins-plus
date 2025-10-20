---
name: ai-monitoring-setup
type: command
description: Set up comprehensive LLM monitoring, cost tracking, and observability
category: ai
version: 1.0.0
author: Jeremy Longshore
shortcut: ams
estimated_time: 5-10 minutes
---

# AI Monitoring Setup

Generate complete LLM monitoring infrastructure with cost tracking, performance metrics, error logging, and alerting for production AI applications.

## What You'll Get

When you run this command, you'll receive:

1. **Cost tracking** with real-time budget monitoring
2. **Performance metrics** (latency, throughput, success rate)
3. **Token usage analytics** per model, user, endpoint
4. **Error logging and alerting** (Sentry, Slack, PagerDuty)
5. **Prometheus metrics** for Grafana dashboards
6. **Custom dashboards** with pre-built visualizations
7. **Alerting rules** for cost spikes, errors, latency
8. **OpenTelemetry integration** for distributed tracing

## Usage

```
/ai-monitoring-setup <monitoring_stack>
```

**Monitoring Stacks:** `prometheus`, `datadog`, `newrelic`, `comprehensive`

**Examples:**
- `/ams prometheus` - Prometheus + Grafana stack
- `/ams datadog` - DataDog integration
- `/ams comprehensive` - Full observability stack (Prometheus + Sentry + Logging)

## Generated Output

### Example: Comprehensive Monitoring Stack

**Input:**
```
/ams comprehensive
```

**Output:**

#### 1. Project Structure

```
llm-monitoring/
├── monitoring/
│   ├── __init__.py
│   ├── metrics.py              # Prometheus metrics
│   ├── cost_tracker.py         # Cost tracking and budgets
│   ├── logger.py               # Structured logging
│   ├── tracer.py               # OpenTelemetry tracing
│   └── alerting.py             # Alert management
├── dashboards/
│   ├── grafana/
│   │   ├── llm_overview.json
│   │   ├── cost_analysis.json
│   │   └── performance.json
│   └── prometheus/
│       └── alerts.yml
├── docker/
│   ├── prometheus.yml
│   ├── grafana-datasources.yml
│   └── docker-compose.yml
├── config/
│   ├── __init__.py
│   └── monitoring_config.py
├── requirements.txt
└── README.md
```

#### 2. Cost Tracker (monitoring/cost_tracker.py)

```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

@dataclass
class CostTracker:
    """Track LLM costs with budget alerts."""

    monthly_budget: float = 1000.0  # USD
    alert_thresholds: List[float] = field(default_factory=lambda: [0.5, 0.75, 0.9])

    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "gemini-pro": {"input": 0.50, "output": 1.50}
    }

    def __post_init__(self):
        self.usage_history: List[Dict] = []
        self.current_month_cost: float = 0.0
        self.last_alert_threshold: Optional[float] = None

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for request."""
        rates = self.PRICING.get(model, self.PRICING["gpt-3.5-turbo"])

        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]

        return input_cost + output_cost

    def log_request(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency: float,
        success: bool,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> Dict:
        """Log request and return cost + budget status."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        # Update month cost
        self.current_month_cost += cost

        # Log to history
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "latency": latency,
            "success": success,
            "user_id": user_id,
            "endpoint": endpoint
        }
        self.usage_history.append(log_entry)

        # Check budget alerts
        budget_pct = self.current_month_cost / self.monthly_budget
        alert = self._check_budget_alert(budget_pct)

        return {
            "cost": cost,
            "total_month_cost": self.current_month_cost,
            "budget_used_pct": budget_pct,
            "budget_remaining": self.monthly_budget - self.current_month_cost,
            "alert": alert
        }

    def _check_budget_alert(self, budget_pct: float) -> Optional[Dict]:
        """Check if budget alert threshold crossed."""
        for threshold in sorted(self.alert_thresholds, reverse=True):
            if budget_pct >= threshold and (
                self.last_alert_threshold is None or
                threshold > self.last_alert_threshold
            ):
                self.last_alert_threshold = threshold

                return {
                    "level": "critical" if threshold >= 0.9 else "warning",
                    "message": f"Budget {threshold*100}% used (${self.current_month_cost:.2f} / ${self.monthly_budget:.2f})",
                    "threshold": threshold,
                    "current_cost": self.current_month_cost
                }

        return None

    def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "model"
    ) -> Dict:
        """Get aggregate statistics."""
        filtered_history = self._filter_history(start_date, end_date)

        if not filtered_history:
            return {"total_requests": 0, "total_cost": 0.0}

        total_cost = sum(entry["cost"] for entry in filtered_history)
        total_requests = len(filtered_history)
        successful_requests = sum(1 for entry in filtered_history if entry["success"])
        avg_latency = sum(entry["latency"] for entry in filtered_history) / total_requests

        stats = {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / total_requests,
            "total_cost": total_cost,
            "avg_cost_per_request": total_cost / total_requests,
            "avg_latency": avg_latency,
            "total_tokens": {
                "input": sum(e["input_tokens"] for e in filtered_history),
                "output": sum(e["output_tokens"] for e in filtered_history)
            }
        }

        # Group by model, user, or endpoint
        if group_by:
            grouped = {}
            for entry in filtered_history:
                key = entry.get(group_by, "unknown")
                if key not in grouped:
                    grouped[key] = {"requests": 0, "cost": 0.0}
                grouped[key]["requests"] += 1
                grouped[key]["cost"] += entry["cost"]

            stats[f"by_{group_by}"] = grouped

        return stats

    def _filter_history(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict]:
        """Filter history by date range."""
        if not start_date and not end_date:
            return self.usage_history

        filtered = []
        for entry in self.usage_history:
            timestamp = datetime.fromisoformat(entry["timestamp"])

            if start_date and timestamp < start_date:
                continue
            if end_date and timestamp > end_date:
                continue

            filtered.append(entry)

        return filtered

    def reset_month(self):
        """Reset monthly cost (call at start of each month)."""
        self.current_month_cost = 0.0
        self.last_alert_threshold = None

    def export_history(self, filepath: str):
        """Export usage history to JSON."""
        with open(filepath, 'w') as f:
            json.dump(self.usage_history, f, indent=2)
```

#### 3. Prometheus Metrics (monitoring/metrics.py)

```python
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps

# Metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['model', 'endpoint', 'status']
)

llm_request_duration = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['model', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total tokens used',
    ['model', 'type']  # type: input or output
)

llm_cost_total = Counter(
    'llm_cost_total_usd',
    'Total cost in USD',
    ['model']
)

llm_errors_total = Counter(
    'llm_errors_total',
    'Total LLM errors',
    ['model', 'error_type']
)

llm_active_requests = Gauge(
    'llm_active_requests',
    'Currently active LLM requests',
    ['model']
)

llm_budget_remaining = Gauge(
    'llm_budget_remaining_usd',
    'Remaining monthly budget in USD'
)

llm_info = Info(
    'llm_version',
    'LLM API version and configuration'
)

class MetricsCollector:
    """Collect and export Prometheus metrics."""

    def __init__(self, cost_tracker):
        self.cost_tracker = cost_tracker

    def track_request(self, model: str, endpoint: str = "default"):
        """Decorator to track LLM requests."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Increment active requests
                llm_active_requests.labels(model=model).inc()

                start_time = time.time()
                status = "success"
                error_type = None

                try:
                    result = await func(*args, **kwargs)

                    # Track tokens
                    if "usage" in result:
                        llm_tokens_total.labels(
                            model=model,
                            type="input"
                        ).inc(result["usage"]["input_tokens"])

                        llm_tokens_total.labels(
                            model=model,
                            type="output"
                        ).inc(result["usage"]["output_tokens"])

                        # Track cost
                        cost = self.cost_tracker.calculate_cost(
                            model=model,
                            input_tokens=result["usage"]["input_tokens"],
                            output_tokens=result["usage"]["output_tokens"]
                        )
                        llm_cost_total.labels(model=model).inc(cost)

                    return result

                except Exception as e:
                    status = "error"
                    error_type = type(e).__name__

                    llm_errors_total.labels(
                        model=model,
                        error_type=error_type
                    ).inc()

                    raise

                finally:
                    # Record duration
                    duration = time.time() - start_time
                    llm_request_duration.labels(
                        model=model,
                        endpoint=endpoint
                    ).observe(duration)

                    # Record total requests
                    llm_requests_total.labels(
                        model=model,
                        endpoint=endpoint,
                        status=status
                    ).inc()

                    # Decrement active requests
                    llm_active_requests.labels(model=model).dec()

                    # Update budget gauge
                    llm_budget_remaining.set(
                        self.cost_tracker.monthly_budget -
                        self.cost_tracker.current_month_cost
                    )

            return wrapper
        return decorator

# Usage
metrics = MetricsCollector(cost_tracker=CostTracker())

@metrics.track_request(model="claude-3-haiku-20240307", endpoint="chat")
async def generate_response(prompt: str):
    response = await llm.complete(prompt)
    return {
        "content": response.content,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens
        }
    }
```

#### 4. Structured Logging (monitoring/logger.py)

```python
import logging
import json
from datetime import datetime
from typing import Any, Dict

class StructuredLogger:
    """JSON structured logging for LLM operations."""

    def __init__(self, name: str = "llm-app"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(self.JSONFormatter())
        self.logger.addHandler(handler)

    class JSONFormatter(logging.Formatter):
        """Format logs as JSON."""
        def format(self, record):
            log_obj = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName
            }

            # Add custom fields
            if hasattr(record, "extra"):
                log_obj.update(record.extra)

            return json.dumps(log_obj)

    def log_request(
        self,
        model: str,
        prompt: str,
        response: str,
        tokens: Dict,
        cost: float,
        latency: float,
        success: bool,
        user_id: str = None
    ):
        """Log LLM request."""
        self.logger.info(
            "LLM Request",
            extra={
                "type": "llm_request",
                "model": model,
                "prompt_preview": prompt[:100],
                "response_preview": response[:100],
                "tokens": tokens,
                "cost": cost,
                "latency": latency,
                "success": success,
                "user_id": user_id
            }
        )

    def log_error(
        self,
        model: str,
        error: Exception,
        context: Dict
    ):
        """Log LLM error."""
        self.logger.error(
            f"LLM Error: {str(error)}",
            extra={
                "type": "llm_error",
                "model": model,
                "error_type": type(error).__name__,
                "error_message": str(error),
                **context
            }
        )

    def log_budget_alert(self, alert: Dict):
        """Log budget alert."""
        self.logger.warning(
            alert["message"],
            extra={
                "type": "budget_alert",
                **alert
            }
        )

# Usage
logger = StructuredLogger()

logger.log_request(
    model="claude-3-haiku",
    prompt="What is AI?",
    response="AI is...",
    tokens={"input": 10, "output": 50},
    cost=0.0001,
    latency=1.2,
    success=True,
    user_id="user-123"
)
```

#### 5. Alerting (monitoring/alerting.py)

```python
import requests
from typing import Dict, Optional
from enum import Enum

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertManager:
    """Send alerts to various channels."""

    def __init__(
        self,
        slack_webhook: Optional[str] = None,
        pagerduty_key: Optional[str] = None,
        email_config: Optional[Dict] = None
    ):
        self.slack_webhook = slack_webhook
        self.pagerduty_key = pagerduty_key
        self.email_config = email_config

    def send_alert(
        self,
        message: str,
        level: AlertLevel = AlertLevel.WARNING,
        details: Optional[Dict] = None
    ):
        """Send alert to configured channels."""
        if level == AlertLevel.CRITICAL and self.pagerduty_key:
            self._send_pagerduty(message, details)

        if level in [AlertLevel.WARNING, AlertLevel.CRITICAL] and self.slack_webhook:
            self._send_slack(message, level, details)

    def _send_slack(
        self,
        message: str,
        level: AlertLevel,
        details: Optional[Dict]
    ):
        """Send Slack notification."""
        color = {
            AlertLevel.INFO: "#36a64f",
            AlertLevel.WARNING: "#ff9900",
            AlertLevel.CRITICAL: "#ff0000"
        }[level]

        payload = {
            "attachments": [{
                "color": color,
                "title": f"{level.value.upper()}: LLM Monitoring Alert",
                "text": message,
                "fields": [
                    {"title": key, "value": str(value), "short": True}
                    for key, value in (details or {}).items()
                ],
                "footer": "LLM Monitoring System",
                "ts": int(time.time())
            }]
        }

        requests.post(self.slack_webhook, json=payload)

    def _send_pagerduty(self, message: str, details: Optional[Dict]):
        """Trigger PagerDuty incident."""
        payload = {
            "routing_key": self.pagerduty_key,
            "event_action": "trigger",
            "payload": {
                "summary": message,
                "severity": "critical",
                "source": "llm-monitoring",
                "custom_details": details or {}
            }
        }

        requests.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=payload
        )

    def budget_alert(self, budget_info: Dict):
        """Send budget alert."""
        level = AlertLevel.CRITICAL if budget_info["threshold"] >= 0.9 else AlertLevel.WARNING

        self.send_alert(
            message=f"LLM Budget Alert: {budget_info['threshold']*100}% used",
            level=level,
            details={
                "Current Cost": f"${budget_info['current_cost']:.2f}",
                "Monthly Budget": f"${budget_info.get('monthly_budget', 0):.2f}",
                "Remaining": f"${budget_info.get('budget_remaining', 0):.2f}"
            }
        )

    def error_spike_alert(self, error_count: int, time_window: str):
        """Alert on error spike."""
        self.send_alert(
            message=f"LLM Error Spike Detected: {error_count} errors in {time_window}",
            level=AlertLevel.WARNING,
            details={
                "Error Count": error_count,
                "Time Window": time_window
            }
        )

    def latency_alert(self, model: str, latency_p95: float):
        """Alert on high latency."""
        self.send_alert(
            message=f"High Latency Detected for {model}",
            level=AlertLevel.WARNING,
            details={
                "Model": model,
                "P95 Latency": f"{latency_p95:.2f}s"
            }
        )

# Usage
alerts = AlertManager(
    slack_webhook="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    pagerduty_key="your-pagerduty-key"
)

# Budget alert
if budget_alert:
    alerts.budget_alert(budget_alert)

# Error spike
if error_count > 10:
    alerts.error_spike_alert(error_count=15, time_window="5 minutes")
```

#### 6. Grafana Dashboards (dashboards/grafana/llm_overview.json)

```json
{
  "dashboard": {
    "title": "LLM Overview",
    "panels": [
      {
        "title": "Total Requests",
        "targets": [{
          "expr": "sum(rate(llm_requests_total[5m]))"
        }],
        "type": "graph"
      },
      {
        "title": "Cost (Last 24h)",
        "targets": [{
          "expr": "sum(increase(llm_cost_total_usd[24h]))"
        }],
        "type": "singlestat"
      },
      {
        "title": "Success Rate",
        "targets": [{
          "expr": "sum(rate(llm_requests_total{status=\"success\"}[5m])) / sum(rate(llm_requests_total[5m]))"
        }],
        "type": "gauge"
      },
      {
        "title": "P95 Latency by Model",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(llm_request_duration_seconds_bucket[5m]))"
        }],
        "type": "graph"
      },
      {
        "title": "Budget Remaining",
        "targets": [{
          "expr": "llm_budget_remaining_usd"
        }],
        "type": "gauge"
      }
    ]
  }
}
```

#### 7. Docker Compose (docker/docker-compose.yml)

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    volumes:
      - ./grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasource.yml
      - ../dashboards/grafana:/etc/grafana/provisioning/dashboards
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus

  alertmanager:
    image: prom/alertmanager:latest
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"

volumes:
  prometheus-data:
  grafana-data:
```

## Features Included

**Cost Management:**
-  Real-time cost tracking per request
-  Budget alerts (50%, 75%, 90% thresholds)
-  Cost breakdown by model, user, endpoint
-  Monthly cost reset automation

**Performance Monitoring:**
-  Request latency (P50, P95, P99)
-  Throughput (requests per second)
-  Success rate tracking
-  Active request count

**Resource Tracking:**
-  Token usage (input/output)
-  Model usage distribution
-  Per-user analytics

**Alerting:**
-  Slack notifications
-  PagerDuty integration (critical)
-  Custom alert rules
-  Error spike detection

**Visualization:**
-  Grafana dashboards
-  Cost analysis
-  Performance metrics
-  Real-time monitoring

## Time Savings

**Manual setup:** 12-16 hours
- Metrics instrumentation
- Cost tracking logic
- Logging setup
- Dashboard creation
- Alerting configuration

**With this command:** 5-10 minutes
- Run command
- Configure API keys
- Deploy monitoring stack

**ROI:** 72-96x time multiplier

---

**Next Steps:**
1. Run `/ams comprehensive`
2. Copy generated code to your project
3. Set environment variables (Slack webhook, PagerDuty key)
4. Deploy: `docker-compose up -d`
5. Access Grafana: `http://localhost:3000` (admin/admin)
6. View metrics: `http://localhost:9090`
7. Integrate with your LLM application

**Production checklist:**
- [ ] Configure budget thresholds
- [ ] Set up Slack webhook
- [ ] Configure PagerDuty for critical alerts
- [ ] Test alert triggers
- [ ] Set up data retention policies
- [ ] Configure backup for metrics data
- [ ] Create custom dashboards for your use cases

**Estimated monitoring cost:** $0-$50/month (infrastructure costs for Prometheus + Grafana)
