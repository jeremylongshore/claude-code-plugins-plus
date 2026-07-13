# Log Analysis

## Log Analysis

### Parse Debug Log

```python
def analyze_debug_log(log_file: str):
    """Analyze debug log file."""
    with open(log_file) as f:
        content = f.read()

    entries = content.split("---\n")
    requests = []
    responses = []
    errors = []

    for entry in entries:
        if not entry.strip():
            continue
        try:
            data = json.loads(entry)
            if data["type"] == "request":
                requests.append(data)
            elif data["type"] == "response":
                responses.append(data)
            elif data["type"] == "error":
                errors.append(data)
        except:
            pass

    return {
        "total_requests": len(requests),
        "successful": len(responses),
        "failed": len(errors),
        "error_rate": len(errors) / max(len(requests), 1),
        "avg_latency": sum(r["elapsed_seconds"] for r in responses) / max(len(responses), 1),
        "error_types": list(set(e["error_type"] for e in errors))
    }
```
