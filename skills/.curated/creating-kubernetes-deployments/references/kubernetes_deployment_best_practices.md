# Kubernetes Deployment Best Practices

Production-ready deployment guidelines for reliability, scalability, and maintainability.

## Resource Management

### Always Set Resource Requests and Limits

```yaml
resources:
  requests:
    cpu: 100m       # Minimum guaranteed
    memory: 256Mi   # Minimum guaranteed
  limits:
    cpu: 500m       # Maximum allowed
    memory: 512Mi   # Maximum allowed (OOMKilled if exceeded)
```

**Guidelines:**

- Requests = typical usage (for scheduling)
- Limits = maximum acceptable (for protection)
- Memory limits are hard - exceeding causes OOMKill
- CPU limits are soft - throttled, not killed

### Resource Sizing by Workload

| Workload | CPU Request | Memory Request | CPU Limit | Memory Limit |
|----------|-------------|----------------|-----------|--------------|
| Static frontend | 10m-50m | 32Mi-64Mi | 100m-200m | 128Mi |
| REST API | 100m-500m | 256Mi-512Mi | 500m-1000m | 1Gi |
| Background worker | 250m-1000m | 512Mi-1Gi | 2000m | 2Gi |
| Database | 500m-2000m | 1Gi-4Gi | 4000m | 8Gi |
| ML inference | 1000m-4000m | 2Gi-8Gi | 8000m | 16Gi |

---

## Health Checks

### Implement All Three Probe Types

```yaml
# Liveness: Is the container running?
# Fails → Container restarted
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

# Readiness: Is the container ready for traffic?
# Fails → Removed from Service endpoints
readinessProbe:
  httpGet:
    path: /readyz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  successThreshold: 1
  failureThreshold: 3

# Startup: For slow-starting containers
# Fails during startup → Container restarted
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

### Probe Guidelines

| Setting | Liveness | Readiness | Startup |
|---------|----------|-----------|---------|
| initialDelaySeconds | App startup time | 0-5 | 0 |
| periodSeconds | 10-30 | 5-10 | 10 |
| timeoutSeconds | 5 | 5 | 5 |
| failureThreshold | 3 | 3 | 30 (slow apps) |

**Don'ts:**

- Don't make liveness probes depend on external services
- Don't make readiness probes too expensive
- Don't set initialDelaySeconds too low

---

## Deployment Strategy

### Rolling Updates (Default)

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Extra pods during update
      maxUnavailable: 25%  # Unavailable pods during update
```

**Configurations:**

- **Aggressive:** maxSurge: 100%, maxUnavailable: 0 (zero downtime, double resources)
- **Conservative:** maxSurge: 1, maxUnavailable: 0 (slow but safe)
- **Balanced:** maxSurge: 25%, maxUnavailable: 25% (default)

### When to Use Recreate

```yaml
spec:
  strategy:
    type: Recreate
```

Use Recreate when:

- Application can't run multiple versions simultaneously
- Database migrations require exclusive access
- Resource constraints prevent double deployment

---

## High Availability

### Run Multiple Replicas

```yaml
spec:
  replicas: 3  # Minimum for HA
```

**Guidelines:**

- Minimum 3 replicas for production
- Odd numbers for quorum-based apps
- Consider traffic patterns for worker scaling

### Spread Across Zones

```yaml
spec:
  template:
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: my-app
```

### Pod Anti-Affinity

```yaml
spec:
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: my-app
              topologyKey: kubernetes.io/hostname
```

### PodDisruptionBudget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-app-pdb
spec:
  minAvailable: 2  # or maxUnavailable: 1
  selector:
    matchLabels:
      app: my-app
```

---

## Configuration Management

### Use ConfigMaps for Non-Sensitive Config

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "info"
  API_TIMEOUT: "30"
  FEATURE_FLAGS: |
    {
      "newFeature": true,
      "betaMode": false
    }
```

### Use Secrets for Sensitive Data

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgres://user:pass@host/db"
  API_KEY: "secret-key-here"
```

### Mount as Environment or Files

```yaml
# As environment variables
envFrom:
- configMapRef:
    name: app-config
- secretRef:
    name: app-secrets

# As files
volumeMounts:
- name: config-volume
  mountPath: /etc/config
volumes:
- name: config-volume
  configMap:
    name: app-config
```

### Configuration Reload Strategies

1. **Restart pods on config change:**

   ```yaml
   annotations:
     configmap-hash: {{ .Values.config | toYaml | sha256sum }}
   ```

2. **Use Reloader controller:**

   ```yaml
   annotations:
     reloader.stakater.com/auto: "true"
   ```

3. **Application-level watching:**
   - Mount as file, watch for changes
   - Use SIGHUP for reload

---

## Image Management

### Use Specific Tags (Not Latest)

```yaml
# Good
image: my-app:v1.2.3
image: my-app:sha-abc1234

# Bad
image: my-app:latest
image: my-app
```

### Set ImagePullPolicy

```yaml
imagePullPolicy: IfNotPresent  # Default for versioned tags
imagePullPolicy: Always        # For :latest or mutable tags
imagePullPolicy: Never         # For local development
```

### Use Private Registry Credentials

```yaml
spec:
  imagePullSecrets:
  - name: registry-credentials
```

---

## Labels and Annotations

### Recommended Labels

```yaml
metadata:
  labels:
    app.kubernetes.io/name: my-api
    app.kubernetes.io/version: "1.2.3"
    app.kubernetes.io/component: backend
    app.kubernetes.io/part-of: my-system
    app.kubernetes.io/managed-by: kubectl
    environment: production
    team: platform
```

### Useful Annotations

```yaml
metadata:
  annotations:
    description: "Main API service"
    owner: "platform-team@company.com"
    repository: "github.com/org/repo"
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
```

---

## Graceful Shutdown

### Configure terminationGracePeriodSeconds

```yaml
spec:
  template:
    spec:
      terminationGracePeriodSeconds: 60  # Default is 30
      containers:
      - name: app
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 10"]
```

### Application Shutdown Handling

1. SIGTERM received by application
2. preStop hook executes (if defined)
3. Container removed from Service endpoints
4. Application should:
   - Stop accepting new requests
   - Finish in-flight requests
   - Close database connections
   - Exit gracefully

---

## Monitoring and Observability

### Expose Metrics Endpoint

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/path: "/metrics"
  prometheus.io/port: "8080"
```

### Standard Metrics to Expose

- Request count and latency
- Error rates
- Resource utilization
- Business metrics

### Structured Logging

```json
{
  "timestamp": "2025-01-19T10:30:00Z",
  "level": "info",
  "message": "Request processed",
  "request_id": "abc123",
  "duration_ms": 45,
  "status_code": 200
}
```

---

## Security Checklist

- [ ] Non-root user in container
- [ ] Read-only root filesystem
- [ ] No privileged containers
- [ ] Resource limits set
- [ ] Network policies defined
- [ ] Secrets not in environment (use mounted files)
- [ ] Image from trusted registry
- [ ] ServiceAccount with minimal permissions
- [ ] Security context configured

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
```

---

## Pre-Deployment Checklist

### Manifest Quality

- [ ] Resource requests and limits defined
- [ ] Health probes configured
- [ ] Labels applied (app, version, env)
- [ ] Namespace specified
- [ ] Image tag is specific (not :latest)

### High Availability

- [ ] Multiple replicas (3+)
- [ ] PodDisruptionBudget created
- [ ] Pod anti-affinity configured
- [ ] Topology spread constraints set

### Operations

- [ ] ConfigMaps/Secrets externalized
- [ ] Metrics endpoint exposed
- [ ] Logging configured
- [ ] Graceful shutdown implemented

### Security

- [ ] Security context set
- [ ] Network policies defined
- [ ] Service account configured
- [ ] Secrets managed properly
