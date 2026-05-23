# Debug Utilities

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
