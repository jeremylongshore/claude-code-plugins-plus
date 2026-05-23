# Inspection Categories

## Inspection Categories

### 1. Runtime Configuration ✅

- Model selection (Gemini 2.5 Pro/Flash)
- Tools enabled (Code Execution, Memory Bank, custom)
- VPC configuration
- Resource allocation
- Scaling policies

### 2. Code Execution Sandbox 🔒

- **Security**: Isolated environment, no external network access
- **State Persistence**: TTL validation (1-14 days)
- **IAM**: Least privilege permissions
- **Performance**: Timeout and resource limits
- **Concurrent Executions**: Max concurrent code runs

**Critical Checks**:

```
✅ State TTL between 7-14 days (optimal for production)
✅ Sandbox type is SECURE_ISOLATED
✅ IAM permissions limited to required GCP services only
✅ Timeout configured appropriately
⚠️ State TTL < 7 days may cause premature session loss
❌ State TTL > 14 days not allowed by Agent Engine
```

### 3. Memory Bank Configuration 🧠

- **Enabled Status**: Persistent memory active
- **Retention Policy**: Max memories, retention days
- **Storage Backend**: Firestore encryption & region
- **Query Performance**: Indexing, caching, latency
- **Auto-Cleanup**: Quota management

**Critical Checks**:

```
✅ Max memories >= 100 (prevents conversation truncation)
✅ Indexing enabled (fast query performance)
✅ Auto-cleanup enabled (prevents quota exhaustion)
✅ Encrypted at rest (Firestore default)
⚠️ Low memory limit may truncate long conversations
```

### 4. A2A Protocol Compliance 🔗

- **AgentCard**: Available at `/.well-known/agent-card`
- **Task API**: `POST /v1/tasks:send` responds correctly
- **Status API**: `GET /v1/tasks/{task_id}` accessible
- **Protocol Version**: 1.0 compliance
- **Required Fields**: name, description, tools, version

**Compliance Report**:

```
✅ AgentCard accessible and valid
✅ Task submission API functional
✅ Status polling API functional
✅ Protocol version 1.0
❌ Missing AgentCard fields: [...]
❌ Task API not responding (check IAM/networking)
```

### 5. Security Posture 🛡️

- **IAM Roles**: Least privilege validation
- **VPC Service Controls**: Perimeter protection
- **Model Armor**: Prompt injection protection
- **Encryption**: At-rest and in-transit
- **Service Account**: Proper configuration
- **Secret Management**: No hardcoded credentials

**Security Score**:

```
🟢 SECURE (90-100%): Production ready
🟡 NEEDS ATTENTION (70-89%): Address issues before prod
🔴 INSECURE (<70%): Do not deploy to production
```

### 6. Performance Metrics 📊

- **Auto-Scaling**: Min/max instances configured
- **Resource Limits**: CPU, memory appropriate
- **Latency**: P50, P95, P99 within SLOs
- **Throughput**: Requests per second
- **Token Usage**: Cost tracking
- **Error Rate**: < 5% target

**Health Status**:

```
🟢 HEALTHY: Error rate < 5%, latency < 3s (p95)
🟡 DEGRADED: Error rate 5-10% or latency 3-5s
🔴 UNHEALTHY: Error rate > 10% or latency > 5s
```

### 7. Monitoring & Observability 📈

- **Cloud Monitoring**: Dashboards configured
- **Alerting**: Policies for errors, latency, costs
- **Logging**: Structured logs aggregated
- **Tracing**: OpenTelemetry enabled
- **Error Tracking**: Cloud Error Reporting

**Observability Score**:

```
✅ All 5 pillars configured: Metrics, Logs, Traces, Alerts, Dashboards
⚠️ Missing alerts for critical scenarios
❌ No monitoring configured (production blocker)
```
