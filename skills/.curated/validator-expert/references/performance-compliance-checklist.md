# Performance (25% Weight) & Compliance (15% Weight) Checklists

---

## Performance Validation

### Auto-Scaling

- Auto-scaling enabled for Agent Engine
- Min/max replicas configured appropriately
- CPU/memory targets set
- Scale-up/scale-down thresholds tuned

### Caching

- Memory Bank caching enabled
- Cache hit rate >60%
- Cache TTL configured
- Response caching for frequent queries

### Resource Limits

- Memory limits appropriate for workload
- CPU allocation sufficient
- Timeout values configured
- Concurrent request limits set

### Code Execution Sandbox

- Sandbox state persistence TTL configured (1-14 days)
- Execution timeout appropriate
- Artifact storage configured
- Resource isolation enabled

### Validation

```python
def validate_performance(agent_config):
    checks = []
    runtime_config = agent_config.get('runtime_config', {})
    auto_scaling = runtime_config.get('auto_scaling', {})
    if not auto_scaling.get('enabled'):
        checks.append({
            "category": "Performance", "check": "Auto-Scaling",
            "status": "WARNING", "message": "Auto-scaling not enabled"
        })
    code_exec = runtime_config.get('code_execution_config', {})
    ttl_days = code_exec.get('state_persistence_ttl_days', 0)
    if ttl_days < 1 or ttl_days > 14:
        checks.append({
            "category": "Performance", "check": "Code Execution TTL",
            "status": "FAIL", "message": f"TTL must be 1-14 days, got {ttl_days}"
        })
    return checks
```

---

## Compliance Validation

### Audit Logging

- Cloud Audit Logs enabled
- Admin activity logged
- Data access logs enabled for sensitive operations
- Log retention >1 year for compliance

### Data Residency

- Agent deployed in compliant region
- Data storage in approved locations
- Cross-border data transfer documented
- Regional data processing requirements met

### Privacy

- PII handling policies implemented
- User consent mechanisms in place
- Data anonymization for non-prod environments
- Right to deletion implemented

### Backup & DR

- Memory Bank backup configured
- Disaster recovery plan documented
- RTO/RPO objectives defined
- Backup restoration tested

### Validation

```python
def validate_compliance(project_id):
    """Check audit log configuration for Vertex AI / Agent Engine.

    Verifies that auditConfigs include aiplatform.googleapis.com
    with ADMIN_READ, DATA_READ, and DATA_WRITE enabled.

    CLI equivalent:
      gcloud projects get-iam-policy PROJECT_ID --format=json
      # Look for auditConfigs with service "aiplatform.googleapis.com"
    """
    import subprocess, json
    result = subprocess.run(
        ["gcloud", "projects", "get-iam-policy", project_id, "--format=json"],
        capture_output=True, text=True
    )
    policy = json.loads(result.stdout)
    audit_configs = policy.get("auditConfigs", [])
    ai_audit = next(
        (cfg for cfg in audit_configs
         if cfg.get("service") == "aiplatform.googleapis.com"),
        None
    )
    if not ai_audit:
        return {
            "category": "Compliance", "check": "Audit Logging",
            "status": "FAIL",
            "message": "No audit log config for aiplatform.googleapis.com"
        }
    enabled_types = {
        entry.get("logType") for entry in ai_audit.get("auditLogConfigs", [])
    }
    required = {"ADMIN_READ", "DATA_READ", "DATA_WRITE"}
    missing = required - enabled_types
    if missing:
        return {
            "category": "Compliance", "check": "Audit Logging",
            "status": "WARNING",
            "message": f"Missing audit log types: {', '.join(sorted(missing))}"
        }
    return {
        "category": "Compliance", "check": "Audit Logging",
        "status": "PASS", "message": "Audit logging fully configured"
    }
```

Source: [Cloud Audit Logs](https://cloud.google.com/logging/docs/audit)
