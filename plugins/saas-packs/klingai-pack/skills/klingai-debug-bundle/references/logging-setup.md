# Logging Setup

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
