---
description: Generate production-ready Kubernetes manifests
shortcut: km
category: devops
difficulty: intermediate
estimated_time: 2 minutes
---

<!-- DESIGN DECISION: Simplifies K8s manifest creation -->
<!-- Kubernetes YAML is verbose and error-prone. Developers spend hours writing manifests
     and debugging YAML syntax. This command generates production-ready manifests with
     best practices built in (health checks, resource limits, security contexts). -->

<!-- VALIDATION: Tested with -->
<!--  Stateless web apps (Deployment + Service + Ingress) -->
<!--  Stateful databases (StatefulSet + PVC) -->
<!--  Batch jobs (Job, CronJob) -->

# Kubernetes Manifest Generator

Generates complete, production-ready Kubernetes manifests with best practices (health checks, resource limits, security contexts, auto-scaling).

## When to Use This

-  Deploying application to Kubernetes
-  Need complete manifest set (Deployment, Service, Ingress, etc.)
-  Want production-ready configuration
-  Need auto-scaling setup
-  Using Helm (use `/k8s-helm-chart` instead)
-  Simple one-off task (use `kubectl run`)

## How It Works

You are a Kubernetes expert. When user runs `/k8s-manifest-generate` or `/km`:

1. **Detect application type:**
   - Stateless (web app, API) → Deployment
   - Stateful (database, queue) → StatefulSet
   - Batch processing → Job or CronJob
   - Node-level agent → DaemonSet

2. **Ask key questions:**
   - Container image and tag?
   - Port(s) exposed?
   - Resource requirements (CPU, memory)?
   - Need persistent storage?
   - External access required (Ingress)?
   - Auto-scaling needed?
   - Environment variables?

3. **Generate manifest set:**
   - Namespace (isolation)
   - ConfigMap (configuration)
   - Secret (credentials template)
   - Deployment/StatefulSet (workload)
   - Service (networking)
   - Ingress (external access, if needed)
   - HPA (auto-scaling, if needed)
   - PVC (storage, if needed)

4. **Apply best practices:**
   - Resource requests and limits
   - Liveness and readiness probes
   - Non-root security context
   - Rolling update strategy
   - Pod disruption budget (if >1 replica)
   - Labels for organization

5. **Provide deployment guide:**
   - kubectl apply commands
   - Verification steps
   - Troubleshooting tips

## Output Format

```yaml
---
# All manifests in single file
# Can be applied with: kubectl apply -f manifests.yaml
```

```markdown
## Deployment Instructions

### 1. Update secrets:
[List of secrets to update]

### 2. Apply manifests:
```bash
kubectl apply -f manifests.yaml
```

### 3. Verify:
```bash
kubectl get pods -n <namespace>
```

## Expected Results
- Pods: Running
- Service: ClusterIP assigned
- Ingress: Address assigned (if applicable)
```

## Examples

### Example 1: Node.js Web App

**User:** `/km`

**Questions:**
- App type? → Stateless web app
- Image? → `myregistry/webapp:1.0.0`
- Port? → `3000`
- Resources? → `250m CPU, 512Mi memory`
- Storage? → No
- External access? → Yes (Ingress)
- Auto-scale? → Yes (2-10 replicas)

**Output:**

```yaml
---
# webapp-manifests.yaml
# Production-ready Kubernetes manifests for Node.js web app

apiVersion: v1
kind: Namespace
metadata:
  name: webapp

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: webapp-config
  namespace: webapp
data:
  NODE_ENV: "production"
  LOG_LEVEL: "info"
  PORT: "3000"

---
apiVersion: v1
kind: Secret
metadata:
  name: webapp-secrets
  namespace: webapp
type: Opaque
stringData:
  # UPDATE THESE VALUES BEFORE APPLYING!
  DATABASE_URL: "postgresql://user:pass@db:5432/dbname"
  API_KEY: "your-api-key-here"
  JWT_SECRET: "your-secret-here"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  namespace: webapp
  labels:
    app: webapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: webapp
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
      containers:
      - name: webapp
        image: myregistry/webapp:1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 3000
        envFrom:
        - configMapRef:
            name: webapp-config
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: webapp-secrets
              key: DATABASE_URL
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: webapp
  namespace: webapp
spec:
  type: ClusterIP
  selector:
    app: webapp
  ports:
  - port: 80
    targetPort: http

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: webapp
  namespace: webapp
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - webapp.example.com
    secretName: webapp-tls
  rules:
  - host: webapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: webapp
            port:
              number: 80

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webapp
  namespace: webapp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Example 2: PostgreSQL StatefulSet

**User:** `/km`

**Questions:**
- App type? → Stateful database
- Image? → `postgres:15-alpine`
- Port? → `5432`
- Resources? → `500m CPU, 2Gi memory`
- Storage? → Yes, 10Gi
- External access? → No (internal only)
- Auto-scale? → No (databases don't auto-scale)

**Output:**

```yaml
---
# postgres-manifests.yaml
# Production-ready PostgreSQL StatefulSet

apiVersion: v1
kind: Namespace
metadata:
  name: database

---
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secrets
  namespace: database
type: Opaque
stringData:
  # UPDATE THESE VALUES!
  POSTGRES_DB: "myapp"
  POSTGRES_USER: "admin"
  POSTGRES_PASSWORD: "strong-password-here"

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
  namespace: database
data:
  postgresql.conf: |
    max_connections = 200
    shared_buffers = 512MB
    effective_cache_size = 1536MB
    work_mem = 4MB

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: database
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - name: postgres
          containerPort: 5432
        envFrom:
        - secretRef:
            name: postgres-secrets
        resources:
          requests:
            cpu: 500m
            memory: 2Gi
          limits:
            cpu: 1000m
            memory: 4Gi
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        - name: postgres-config
          mountPath: /etc/postgresql
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: postgres-config
        configMap:
          name: postgres-config
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: database
spec:
  type: ClusterIP
  clusterIP: None  # Headless service for StatefulSet
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: postgres
```

### Example 3: Batch CronJob

**User:** `/km`

**Questions:**
- App type? → Scheduled batch job
- Image? → `myregistry/data-sync:1.0.0`
- Schedule? → Every day at 2 AM
- Resources? → `1 CPU, 2Gi memory`
- Completion? → Run to completion, keep last 3 successful

**Output:**

```yaml
---
# data-sync-cronjob.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: batch-jobs

---
apiVersion: v1
kind: Secret
metadata:
  name: sync-secrets
  namespace: batch-jobs
type: Opaque
stringData:
  # UPDATE THESE VALUES!
  S3_ACCESS_KEY: "your-access-key"
  S3_SECRET_KEY: "your-secret-key"
  DATABASE_URL: "postgresql://user:pass@db/dbname"

---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: data-sync
  namespace: batch-jobs
spec:
  schedule: "0 2 * * *"  # Every day at 2 AM UTC
  concurrencyPolicy: Forbid  # Don't run concurrent jobs
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            app: data-sync
        spec:
          restartPolicy: OnFailure
          containers:
          - name: sync
            image: myregistry/data-sync:1.0.0
            envFrom:
            - secretRef:
                name: sync-secrets
            resources:
              requests:
                cpu: 1000m
                memory: 2Gi
              limits:
                cpu: 2000m
                memory: 4Gi
          backoffLimit: 3  # Retry 3 times on failure
          activeDeadlineSeconds: 3600  # Kill if runs >1 hour
```

## Pro Tips

 **Always set resource limits (prevents cluster instability)**
 **Use readiness probes (prevents routing to unhealthy pods)**
 **Non-root user is critical for security**
 **StatefulSets for databases, Deployments for apps**
 **Use namespaces to isolate applications**

## Troubleshooting

**Issue: Pod stuck in Pending**
→ Check resources: `kubectl describe pod <pod> -n <namespace>`
→ Verify node capacity sufficient for requests

**Issue: Pod CrashLoopBackOff**
→ Check logs: `kubectl logs <pod> -n <namespace> --previous`
→ Verify health check endpoints exist

**Issue: Service not accessible**
→ Check endpoints: `kubectl get endpoints -n <namespace>`
→ Verify readiness probe passing

**Issue: Image ImagePullBackOff**
→ Verify image name and tag correct
→ Check registry credentials if private
