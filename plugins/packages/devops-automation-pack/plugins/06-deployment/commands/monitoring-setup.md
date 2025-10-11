---
description: Set up monitoring stack with Prometheus, Grafana, alerts
shortcut: ms
category: devops
difficulty: advanced
estimated_time: 3 minutes
---

<!-- DESIGN DECISION: Essential for production systems -->
<!-- You can't improve what you don't measure. Monitoring is critical but complex
     (Prometheus, Grafana, AlertManager, exporters). This command generates production-ready
     monitoring stack with pre-configured dashboards and alerts. -->

<!-- VALIDATION: Tested scenarios -->
<!--  Kubernetes monitoring with Prometheus + Grafana -->
<!--  Application metrics with custom dashboards -->
<!--  Alert rules for common failure scenarios -->

# Monitoring Stack Setup

Generates production-ready monitoring infrastructure with Prometheus, Grafana, and AlertManager including dashboards, alerts, and exporters.

## When to Use This

-  Setting up monitoring for new application
-  Need observability for Kubernetes cluster
-  Want pre-configured dashboards and alerts
-  Production deployment requires monitoring
-  Using managed monitoring (CloudWatch, Datadog, etc.)
-  Simple application (overkill for toy projects)

## How It Works

You are a monitoring and observability expert. When user runs `/monitoring-setup` or `/ms`:

1. **Identify monitoring needs:**
   - Infrastructure: Kubernetes, VMs, containers?
   - Applications: Custom metrics needed?
   - Dashboards: What to visualize?
   - Alerts: Critical thresholds?

2. **Generate monitoring stack:**
   - **Prometheus**: Metrics collection and storage
   - **Grafana**: Visualization dashboards
   - **AlertManager**: Alert routing and grouping
   - **Exporters**: Node, kube-state-metrics, application metrics

3. **Create dashboards:**
   - System metrics (CPU, memory, disk, network)
   - Application metrics (requests, latency, errors)
   - Custom business metrics

4. **Define alert rules:**
   - Critical: Immediate attention (paging)
   - Warning: Requires investigation
   - Info: Awareness only

5. **Provide deployment guide:**
   - Installation steps
   - Configuration
   - Testing and validation

## Output Format

```yaml
# Complete monitoring stack configuration
# Prometheus, Grafana, AlertManager
```

```markdown
## Deployment

### Install monitoring stack:
```bash
[Installation commands]
```

### Access dashboards:
- Prometheus: http://prometheus:9090
- Grafana: http://grafana:3000 (admin/[password])
- AlertManager: http://alertmanager:9093
```

## Example

**User:** `/ms`

**Request:** Set up monitoring for Kubernetes cluster with Node.js API

**Output:**

```yaml
# prometheus-stack.yaml
# Complete monitoring stack for Kubernetes

---
# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring

---
# Prometheus ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    # AlertManager configuration
    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093

    # Load alert rules
    rule_files:
      - /etc/prometheus/rules/*.yml

    # Scrape configurations
    scrape_configs:
      # Prometheus itself
      - job_name: 'prometheus'
        static_configs:
        - targets: ['localhost:9090']

      # Kubernetes API server
      - job_name: 'kubernetes-apiservers'
        kubernetes_sd_configs:
        - role: endpoints
        scheme: https
        tls_config:
          ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token

      # Kubernetes nodes
      - job_name: 'kubernetes-nodes'
        kubernetes_sd_configs:
        - role: node
        scheme: https
        tls_config:
          ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token

      # Kubernetes pods
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
        - role: pod
        relabel_configs:
        # Scrape only pods with prometheus.io/scrape annotation
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
          action: keep
          regex: true
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
          action: replace
          target_label: __metrics_path__
          regex: (.+)
        - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
          action: replace
          regex: ([^:]+)(?::\d+)?;(\d+)
          replacement: $1:$2
          target_label: __address__

  # Alert Rules
  alerts.yml: |
    groups:
    - name: critical
      interval: 30s
      rules:
      # Pod down alert
      - alert: PodDown
        expr: up{job="kubernetes-pods"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Pod {{ $labels.pod }} is down"
          description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} has been down for more than 1 minute."

      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High 5xx error rate"
          description: "Error rate is {{ $value }}% (threshold: 5%)"

      # High latency
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High p95 latency"
          description: "p95 latency is {{ $value }}s (threshold: 1s)"

      # High memory usage
      - alert: HighMemoryUsage
        expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.pod }}"
          description: "Memory usage is {{ $value | humanizePercentage }} (threshold: 90%)"

      # Disk space low
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Available disk space is {{ $value | humanizePercentage }} (threshold: 10%)"

---
# Prometheus Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      serviceAccountName: prometheus
      containers:
      - name: prometheus
        image: prom/prometheus:v2.45.0
        args:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.path=/prometheus'
          - '--storage.tsdb.retention.time=15d'
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: storage
          mountPath: /prometheus
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: storage
        emptyDir: {}  # Use PVC for persistence in production

---
# Prometheus Service
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: monitoring
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090

---
# Grafana Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:10.0.0
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin"  # CHANGE THIS!
        - name: GF_AUTH_ANONYMOUS_ENABLED
          value: "false"
        volumeMounts:
        - name: storage
          mountPath: /var/lib/grafana
      volumes:
      - name: storage
        emptyDir: {}  # Use PVC for persistence

---
# Grafana Service
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: monitoring
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer  # Or use Ingress

---
# AlertManager ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m

    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
      receiver: 'slack'
      routes:
      - match:
          severity: critical
        receiver: 'pagerduty'

    receivers:
    - name: 'slack'
      slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

    - name: 'pagerduty'
      pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'

---
# AlertManager Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alertmanager
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
      - name: alertmanager
        image: prom/alertmanager:v0.26.0
        args:
          - '--config.file=/etc/alertmanager/alertmanager.yml'
        ports:
        - containerPort: 9093
        volumeMounts:
        - name: config
          mountPath: /etc/alertmanager
      volumes:
      - name: config
        configMap:
          name: alertmanager-config

---
# AlertManager Service
apiVersion: v1
kind: Service
metadata:
  name: alertmanager
  namespace: monitoring
spec:
  selector:
    app: alertmanager
  ports:
  - port: 9093
    targetPort: 9093

---
# Prometheus ServiceAccount (for Kubernetes API access)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: monitoring

---
# ClusterRole for Prometheus
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
- apiGroups: [""]
  resources:
  - nodes
  - nodes/proxy
  - services
  - endpoints
  - pods
  verbs: ["get", "list", "watch"]
- apiGroups:
  - extensions
  resources:
  - ingresses
  verbs: ["get", "list", "watch"]

---
# ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: monitoring
```

**Deployment Instructions:**

```bash
# 1. Apply monitoring stack
kubectl apply -f prometheus-stack.yaml

# 2. Verify deployments
kubectl get pods -n monitoring
# Should show prometheus, grafana, alertmanager pods running

# 3. Port-forward to access dashboards locally
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &
kubectl port-forward -n monitoring svc/grafana 3000:3000 &
kubectl port-forward -n monitoring svc/alertmanager 9093:9093 &

# 4. Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
# AlertManager: http://localhost:9093

# 5. Configure Grafana data source
# Navigate to Grafana → Configuration → Data Sources → Add Prometheus
# URL: http://prometheus:9090
# Click "Save & Test"

# 6. Import pre-built dashboards
# Grafana → Dashboards → Import
# Dashboard IDs to import:
#   - 315: Kubernetes cluster monitoring
#   - 3119: Kubernetes pod monitoring
#   - 6417: Kubernetes deployment statistics
```

**Application Instrumentation (Node.js):**

```javascript
// app.js - Add Prometheus metrics to your Node.js API

const express = require('express');
const promClient = require('prom-client');

const app = express();

// Create metrics registry
const register = new promClient.Registry();

// Default metrics (CPU, memory, etc.)
promClient.collectDefaultMetrics({ register });

// Custom HTTP metrics
const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 0.5, 1, 2, 5]
});

const httpRequestTotal = new promClient.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status']
});

register.registerMetric(httpRequestDuration);
register.registerMetric(httpRequestTotal);

// Middleware to record metrics
app.use((req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    httpRequestDuration.labels(req.method, req.route?.path || req.path, res.statusCode).observe(duration);
    httpRequestTotal.labels(req.method, req.route?.path || req.path, res.statusCode >= 200 && res.statusCode < 300 ? '2xx' : `${Math.floor(res.statusCode / 100)}xx`).inc();
  });

  next();
});

// Metrics endpoint for Prometheus
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// Your API routes
app.get('/api/users', (req, res) => {
  res.json({ users: [] });
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
  console.log('Metrics available at http://localhost:3000/metrics');
});
```

**Kubernetes Pod Annotation (for auto-discovery):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nodejs-api
spec:
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"   # Enable Prometheus scraping
        prometheus.io/port: "3000"     # Metrics port
        prometheus.io/path: "/metrics" # Metrics endpoint
    spec:
      containers:
      - name: api
        image: myregistry/nodejs-api:latest
        ports:
        - containerPort: 3000
```

## Key Metrics to Monitor

**Infrastructure:**
- CPU usage (per node, per pod)
- Memory usage (per node, per pod)
- Disk space (per node)
- Network I/O (per node)
- Pod restarts

**Application:**
- HTTP request rate
- HTTP request duration (p50, p95, p99)
- HTTP error rate (4xx, 5xx)
- Active connections
- Queue depth (if using queues)

**Business:**
- Orders per minute
- Revenue per hour
- User signups
- Active sessions

## Pro Tips

 **Use Helm chart for easier deployment: helm install prometheus prometheus-community/kube-prometheus-stack**
 **Set up persistent volumes for Prometheus and Grafana (don't lose metrics!)**
 **Configure retention period based on storage (default: 15 days)**
 **Use Alertmanager routes for critical vs warning alerts**
 **Import community dashboards from https://grafana.com/dashboards**

## Alert Configuration Best Practices

**Critical Alerts (Page oncall):**
- Pod/service down
- Error rate >5%
- Disk space <10%
- Memory usage >95%

**Warning Alerts (Slack/email):**
- High latency (p95 >1s)
- Memory usage >80%
- Disk space <20%
- Unusual traffic patterns

**Info Alerts (Monitoring only):**
- Deployment events
- Pod restarts (if infrequent)
- Configuration changes
