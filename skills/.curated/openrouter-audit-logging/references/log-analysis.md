# Log Analysis

## Log Analysis

### Query Audit Logs

```python
def query_logs(
    log_dir: str,
    user_id: str = None,
    model: str = None,
    status: str = None,
    start_date: str = None,
    end_date: str = None
) -> list[AuditEntry]:
    """Query audit logs with filters."""
    results = []

    # Get log files in date range
    log_files = sorted(Path(log_dir).glob("audit_*.jsonl"))

    for log_file in log_files:
        file_date = log_file.stem.split("_")[1]

        if start_date and file_date < start_date:
            continue
        if end_date and file_date > end_date:
            continue

        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)

                # Apply filters
                if user_id and entry.get("user_id") != user_id:
                    continue
                if model and entry.get("model") != model:
                    continue
                if status and entry.get("status") != status:
                    continue

                results.append(entry)

    return results

# Example queries
user_logs = query_logs("audit_logs", user_id="user_123")
error_logs = query_logs("audit_logs", status="error")
```

### Generate Audit Report

```python
def generate_audit_report(log_dir: str, days: int = 7) -> dict:
    """Generate audit report for compliance."""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    logs = query_logs(
        log_dir,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )

    # Aggregate statistics
    total_requests = len(logs)
    successful = sum(1 for l in logs if l["status"] == "success")
    failed = sum(1 for l in logs if l["status"] == "error")

    by_user = {}
    by_model = {}
    total_tokens = 0
    total_latency = 0

    for log in logs:
        user = log["user_id"]
        model = log["model"]

        by_user[user] = by_user.get(user, 0) + 1
        by_model[model] = by_model.get(model, 0) + 1
        total_tokens += log["prompt_tokens"] + log["completion_tokens"]
        total_latency += log["latency_ms"]

    return {
        "report_period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "summary": {
            "total_requests": total_requests,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_requests if total_requests else 0,
            "total_tokens": total_tokens,
            "avg_latency_ms": total_latency / total_requests if total_requests else 0
        },
        "by_user": dict(sorted(by_user.items(), key=lambda x: -x[1])),
        "by_model": dict(sorted(by_model.items(), key=lambda x: -x[1])),
        "error_breakdown": {
            log["error_type"]: 1
            for log in logs if log["status"] == "error"
        }
    }
```
