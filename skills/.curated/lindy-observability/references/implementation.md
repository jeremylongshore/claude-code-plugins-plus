# Lindy Observability -- Implementation Details

## Structured Logging

```python
import os
import json
import time
import logging
from datetime import datetime, timezone

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "lindy-integration",
            "env": os.environ.get("LINDY_ENVIRONMENT", "development"),
        }
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())
logger = logging.getLogger("lindy")
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class LindyLogger:
    def __init__(self, agent_id: str, run_id: str | None = None):
        self.agent_id = agent_id
        self.run_id = run_id
        self._start = time.perf_counter()

    def _extra(self, **kwargs) -> dict:
        return {"agent_id": self.agent_id, "run_id": self.run_id, **kwargs}

    def info(self, msg: str, **kwargs):
        record = logger.makeRecord("lindy", logging.INFO, "", 0, msg, (), None)
        record.extra = self._extra(**kwargs)
        logger.handle(record)

    def timing(self, event: str) -> float:
        elapsed = (time.perf_counter() - self._start) * 1000
        self.info(f"{event} completed", latency_ms=round(elapsed, 1))
        return elapsed


log = LindyLogger(agent_id="agent-abc123", run_id="run-xyz789")
log.info("Agent triggered", trigger_type="webhook")
log.timing("agent_execution")
```

## Advanced Patterns

### Metrics Collection

```python
from dataclasses import dataclass, field

@dataclass
class AgentMetrics:
    agent_id: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    _latencies: list = field(default_factory=list, repr=False)

    def record_run(self, success: bool, latency_ms: float) -> None:
        self.total_runs += 1
        self._latencies.append(latency_ms)
        if success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1

    @property
    def success_rate(self) -> float:
        return self.successful_runs / max(1, self.total_runs)

    @property
    def avg_latency_ms(self) -> float:
        return sum(self._latencies) / max(1, len(self._latencies))

    def summary(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "total_runs": self.total_runs,
            "success_rate": f"{self.success_rate:.1%}",
            "avg_latency_ms": round(self.avg_latency_ms, 1),
        }


_metrics: dict[str, AgentMetrics] = {}

def record_agent_run(agent_id: str, success: bool, latency_ms: float) -> None:
    if agent_id not in _metrics:
        _metrics[agent_id] = AgentMetrics(agent_id=agent_id)
    _metrics[agent_id].record_run(success, latency_ms)
```

### Health Check Endpoint

```python
import requests
import os
import time
from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/health/lindy")
def lindy_health():
    try:
        start = time.perf_counter()
        resp = requests.get(
            "https://api.lindy.ai/v1/agents",
            headers={"Authorization": f"Bearer {os.environ['LINDY_API_KEY']}"},
            timeout=5, params={"limit": 1},
        )
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        if resp.status_code == 200:
            return jsonify({"status": "ok", "latency_ms": latency_ms}), 200
        return jsonify({"status": "degraded", "code": resp.status_code}), 503
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 503
```

## Troubleshooting

### Dashboard Shows No Activity Despite Active Runs

1. Verify you are in the correct Lindy workspace
2. Confirm agent IDs in logs match agents in your workspace
3. Check the date range filter in the dashboard
4. Look for shadow agents with duplicate names

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
