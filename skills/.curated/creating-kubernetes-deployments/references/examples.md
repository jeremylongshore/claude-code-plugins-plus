# Kubernetes Deployment Examples

Detailed walkthroughs for common deployment scenarios.

---

## Example 1: REST API with Auto-Scaling

**Request:** "Deploy my Python FastAPI app with auto-scaling and health checks"

### Requirements Gathered

- Application: FastAPI REST API
- Image: `my-registry.io/api:v1.2.0`
- Port: 8000
- Health endpoint: `/health`
- Expected load: 100-1000 req/s

### Generated Manifests

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  labels:
    app: fastapi-app
    version: v1.2.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: fastapi-app
        version: v1.2.0
    spec:
      containers:
      - name: api
        image: my-registry.io/api:v1.2.0
        ports:
        - containerPort: 8000
          name: http
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          successThreshold: 1
        env:
        - name: LOG_LEVEL
          value: "info"
        - name: WORKERS
          value: "4"
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-app
spec:
  type: ClusterIP
  selector:
    app: fastapi-app
  ports:
  - port: 80
    targetPort: 8000
    name: http
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-app
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Deployment Steps

```bash
kubectl apply -f api-deployment.yaml
kubectl rollout status deployment/fastapi-app
kubectl get hpa fastapi-app-hpa
```

### Verification

```bash
# Check pods running
kubectl get pods -l app=fastapi-app

# Test health endpoint
kubectl port-forward svc/fastapi-app 8080:80
curl http://localhost:8080/health

# Watch auto-scaling
kubectl get hpa -w
```

---

## Example 2: Web Application with Ingress and TLS

**Request:** "Deploy React frontend with HTTPS at app.example.com"

### Requirements Gathered

- Application: React SPA served by nginx
- Image: `my-registry.io/frontend:v2.0.0`
- Domain: `app.example.com`
- TLS: Let's Encrypt via cert-manager

### Generated Manifests

```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: nginx
        image: my-registry.io/frontend:v2.0.0
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 2
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  type: ClusterIP
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - app.example.com
    secretName: frontend-tls
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

### Deployment Steps

```bash
# Ensure cert-manager is installed
kubectl get pods -n cert-manager

# Apply manifests
kubectl apply -f frontend-deployment.yaml

# Wait for certificate
kubectl get certificate frontend-tls
```

### Verification

```bash
# Check ingress
kubectl describe ingress frontend-ingress

# Check TLS certificate
kubectl get certificate
kubectl describe certificate frontend-tls

# Test HTTPS
curl -v https://app.example.com/
```

---

## Example 3: Worker Deployment with ConfigMap

**Request:** "Deploy background worker that processes queue messages"

### Requirements Gathered

- Application: Python Celery worker
- Image: `my-registry.io/worker:v1.0.0`
- No external ports (internal worker)
- Needs Redis connection string from ConfigMap

### Generated Manifests

```yaml
# worker-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: worker-config
data:
  REDIS_URL: "redis://redis-master:6379/0"
  CELERY_CONCURRENCY: "4"
  LOG_LEVEL: "info"
  QUEUE_NAME: "default"
---
apiVersion: v1
kind: Secret
metadata:
  name: worker-secrets
type: Opaque
stringData:
  REDIS_PASSWORD: "your-redis-password"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  labels:
    app: celery-worker
spec:
  replicas: 5
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: worker
        image: my-registry.io/worker:v1.0.0
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 1Gi
        envFrom:
        - configMapRef:
            name: worker-config
        - secretRef:
            name: worker-secrets
        # No ports - this is a worker
        # Liveness check via exec
        livenessProbe:
          exec:
            command:
            - celery
            - -A
            - app
            - inspect
            - ping
          initialDelaySeconds: 30
          periodSeconds: 60
          timeoutSeconds: 10
```

### Deployment Steps

```bash
kubectl apply -f worker-config.yaml
kubectl rollout status deployment/celery-worker
```

### Verification

```bash
# Check workers
kubectl get pods -l app=celery-worker

# Check logs
kubectl logs -l app=celery-worker --tail=50

# Scale workers
kubectl scale deployment/celery-worker --replicas=10
```

---

## Example 4: StatefulSet for Database

**Request:** "Deploy PostgreSQL with persistent storage"

### Requirements Gathered

- Application: PostgreSQL 15
- Storage: 100Gi persistent volume
- Single instance (not clustered)
- Backup via CronJob

### Generated Manifests

```yaml
# postgres-statefulset.yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
type: Opaque
stringData:
  POSTGRES_USER: "admin"
  POSTGRES_PASSWORD: "secure-password-here"
  POSTGRES_DB: "myapp"
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  type: ClusterIP
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
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
        - containerPort: 5432
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        envFrom:
        - secretRef:
            name: postgres-secret
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - admin
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - admin
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: standard
      resources:
        requests:
          storage: 100Gi
```

### Deployment Steps

```bash
kubectl apply -f postgres-statefulset.yaml
kubectl rollout status statefulset/postgres
```

### Verification

```bash
# Check PVC
kubectl get pvc

# Connect to database
kubectl exec -it postgres-0 -- psql -U admin -d myapp

# Check data persists after restart
kubectl delete pod postgres-0
kubectl get pod postgres-0 -w
```

---

## Example 5: Microservices with Network Policy

**Request:** "Deploy API and database with network isolation"

### Requirements Gathered

- API can talk to database
- Database only accepts connections from API
- External traffic only to API

### Generated Manifests

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-policy
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api
    ports:
    - protocol: TCP
      port: 5432
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-policy
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector: {}  # Allow from ingress controller
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  - to:  # Allow DNS
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

### Deployment Steps

```bash
kubectl apply -f network-policy.yaml

# Label pods correctly
kubectl label pods -l app=backend app=api --overwrite
```

### Verification

```bash
# Test connectivity from API to DB
kubectl exec -it deploy/api -- nc -zv database 5432

# Test that external access to DB is blocked
kubectl run test --rm -it --image=busybox -- nc -zv database 5432
# Should timeout/fail
```

---

## Example 6: Blue-Green Deployment

**Request:** "Deploy new version with instant rollback capability"

### Requirements Gathered

- Current version: v1.0.0 (blue)
- New version: v2.0.0 (green)
- Zero downtime switch

### Generated Manifests

```yaml
# blue-green.yaml
# Blue deployment (current production)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-blue
  labels:
    app: myapp
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      version: blue
  template:
    metadata:
      labels:
        app: myapp
        version: blue
    spec:
      containers:
      - name: app
        image: my-registry.io/app:v1.0.0
        ports:
        - containerPort: 8080
---
# Green deployment (new version)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-green
  labels:
    app: myapp
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      version: green
  template:
    metadata:
      labels:
        app: myapp
        version: green
    spec:
      containers:
      - name: app
        image: my-registry.io/app:v2.0.0
        ports:
        - containerPort: 8080
---
# Service (switch selector to switch traffic)
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
    version: blue  # Change to 'green' to switch
  ports:
  - port: 80
    targetPort: 8080
```

### Switch to Green

```bash
# Verify green is ready
kubectl get pods -l version=green

# Switch traffic
kubectl patch svc myapp -p '{"spec":{"selector":{"version":"green"}}}'

# Verify
kubectl get endpoints myapp
```

### Rollback to Blue

```bash
kubectl patch svc myapp -p '{"spec":{"selector":{"version":"blue"}}}'
```

---

## Example 7: CronJob for Scheduled Tasks

**Request:** "Run database cleanup job every night at 2 AM"

### Generated Manifests

```yaml
# cleanup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-cleanup
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 3
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: cleanup
            image: my-registry.io/db-tools:v1.0.0
            command:
            - /bin/sh
            - -c
            - |
              echo "Starting cleanup at $(date)"
              psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days'"
              echo "Cleanup completed at $(date)"
            env:
            - name: DB_HOST
              value: "postgres"
            - name: DB_NAME
              value: "myapp"
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: username
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            resources:
              requests:
                cpu: 100m
                memory: 128Mi
              limits:
                cpu: 500m
                memory: 256Mi
```

### Verification

```bash
# Check cronjob
kubectl get cronjob db-cleanup

# Trigger manual run
kubectl create job --from=cronjob/db-cleanup db-cleanup-manual

# Check job status
kubectl get jobs
kubectl logs job/db-cleanup-manual
```

---

## Example 8: Multi-Container Pod (Sidecar Pattern)

**Request:** "Deploy app with log shipping sidecar"

### Generated Manifests

```yaml
# app-with-sidecar.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-logging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: app-with-logging
  template:
    metadata:
      labels:
        app: app-with-logging
    spec:
      containers:
      # Main application
      - name: app
        image: my-registry.io/app:v1.0.0
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: logs
          mountPath: /var/log/app
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 512Mi
      # Log shipping sidecar
      - name: fluentd
        image: fluent/fluentd:v1.16
        volumeMounts:
        - name: logs
          mountPath: /var/log/app
          readOnly: true
        - name: fluentd-config
          mountPath: /fluentd/etc
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
      volumes:
      - name: logs
        emptyDir: {}
      - name: fluentd-config
        configMap:
          name: fluentd-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/app/*.log
      pos_file /var/log/app/app.log.pos
      tag app.logs
      <parse>
        @type json
      </parse>
    </source>
    <match app.**>
      @type elasticsearch
      host elasticsearch
      port 9200
      logstash_format true
    </match>
```

---

## Quick Reference: Common Patterns

| Pattern | Use Case | Key Feature |
|---------|----------|-------------|
| Rolling Update | Zero-downtime updates | `maxSurge`, `maxUnavailable` |
| Blue-Green | Instant rollback | Two deployments, switch Service |
| Canary | Gradual rollout | Multiple deployments with % traffic |
| Sidecar | Log shipping, proxy | Multiple containers in pod |
| Init Container | Setup, migrations | `initContainers` |
| Job | One-time task | `restartPolicy: Never` |
| CronJob | Scheduled tasks | `schedule` in cron format |
| StatefulSet | Databases, stateful apps | Stable network identity, PVC |
| DaemonSet | Node agents | One pod per node |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
