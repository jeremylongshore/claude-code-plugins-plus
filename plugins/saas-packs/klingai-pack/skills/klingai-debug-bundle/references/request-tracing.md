# Request Tracing

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
