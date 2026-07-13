# Kubernetes API Reference

Quick reference for common Kubernetes resource definitions and API versions.

## API Versions

| Resource | API Version | Stable Since |
|----------|-------------|--------------|
| Deployment | apps/v1 | K8s 1.9 |
| StatefulSet | apps/v1 | K8s 1.9 |
| DaemonSet | apps/v1 | K8s 1.9 |
| ReplicaSet | apps/v1 | K8s 1.9 |
| Service | v1 | K8s 1.0 |
| ConfigMap | v1 | K8s 1.2 |
| Secret | v1 | K8s 1.0 |
| PersistentVolumeClaim | v1 | K8s 1.0 |
| Ingress | networking.k8s.io/v1 | K8s 1.19 |
| NetworkPolicy | networking.k8s.io/v1 | K8s 1.7 |
| HorizontalPodAutoscaler | autoscaling/v2 | K8s 1.23 |
| PodDisruptionBudget | policy/v1 | K8s 1.21 |
| Job | batch/v1 | K8s 1.8 |
| CronJob | batch/v1 | K8s 1.21 |
| ServiceAccount | v1 | K8s 1.0 |
| Role | rbac.authorization.k8s.io/v1 | K8s 1.8 |
| ClusterRole | rbac.authorization.k8s.io/v1 | K8s 1.8 |

## Resource Definitions

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <name>
  namespace: <namespace>
  labels:
    app: <app-name>
  annotations:
    description: "Optional description"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: <app-name>
  strategy:
    type: RollingUpdate  # or Recreate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
  minReadySeconds: 0
  revisionHistoryLimit: 10
  progressDeadlineSeconds: 600
  template:
    metadata:
      labels:
        app: <app-name>
    spec:
      serviceAccountName: <sa-name>
      containers:
      - name: <container-name>
        image: <image>:<tag>
        imagePullPolicy: IfNotPresent  # Always, Never
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        env:
        - name: KEY
          value: "value"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: secret-name
              key: key
        envFrom:
        - configMapRef:
            name: config-name
        volumeMounts:
        - name: data
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: pvc-name
      nodeSelector:
        disk: ssd
      affinity:
        nodeAffinity: {}
        podAffinity: {}
        podAntiAffinity: {}
      tolerations:
      - key: "key"
        operator: "Equal"
        value: "value"
        effect: "NoSchedule"
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: <name>
spec:
  type: ClusterIP  # NodePort, LoadBalancer, ExternalName
  selector:
    app: <app-name>
  ports:
  - name: http
    port: 80
    targetPort: 8080
    protocol: TCP
  # For NodePort:
  # - nodePort: 30080
  # For LoadBalancer:
  # loadBalancerIP: <ip>
  # externalTrafficPolicy: Local  # or Cluster
  sessionAffinity: None  # or ClientIP
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: <name>
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - example.com
    secretName: tls-secret
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        pathType: Prefix  # Exact, ImplementationSpecific
        backend:
          service:
            name: api-service
            port:
              number: 80
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: <name>
data:
  KEY: "value"
  config.yaml: |
    nested:
      config: value
binaryData:
  binary-key: <base64-encoded>
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: <name>
type: Opaque  # kubernetes.io/tls, kubernetes.io/dockerconfigjson
data:
  username: YWRtaW4=  # base64 encoded
  password: cGFzc3dvcmQ=
stringData:
  plaintext-key: "value"  # will be encoded
```

### PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: <name>
spec:
  accessModes:
  - ReadWriteOnce  # ReadOnlyMany, ReadWriteMany
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi
  selector:
    matchLabels:
      app: my-app
```

### HorizontalPodAutoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: <name>
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: deployment-name
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

### NetworkPolicy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: <name>
spec:
  podSelector:
    matchLabels:
      app: my-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: trusted
    - podSelector:
        matchLabels:
          app: frontend
    - ipBlock:
        cidr: 172.17.0.0/16
        except:
        - 172.17.1.0/24
    ports:
    - protocol: TCP
      port: 80
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

### PodDisruptionBudget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: <name>
spec:
  selector:
    matchLabels:
      app: my-app
  minAvailable: 2     # or use maxUnavailable
  # maxUnavailable: 1
```

### StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: <name>
spec:
  serviceName: headless-service
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0
  podManagementPolicy: OrderedReady  # or Parallel
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: image:tag
        volumeMounts:
        - name: data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: standard
      resources:
        requests:
          storage: 10Gi
```

### Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: <name>
spec:
  completions: 1
  parallelism: 1
  backoffLimit: 3
  activeDeadlineSeconds: 600
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      restartPolicy: Never  # or OnFailure
      containers:
      - name: job
        image: image:tag
        command: ["./run.sh"]
```

### CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: <name>
spec:
  schedule: "0 2 * * *"  # At 2 AM daily
  concurrencyPolicy: Forbid  # Allow, Replace
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  startingDeadlineSeconds: 600
  suspend: false
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: cron
            image: image:tag
```

## Label Conventions

| Label | Purpose | Example |
|-------|---------|---------|
| app | Application name | `app: my-api` |
| version | Application version | `version: v1.2.0` |
| component | Component within app | `component: frontend` |
| part-of | Parent application | `part-of: my-system` |
| managed-by | Tool managing resource | `managed-by: helm` |
| environment | Deployment environment | `environment: production` |

## Resource Naming

- **Max length:** 253 characters (DNS subdomain)
- **Allowed characters:** lowercase alphanumeric, `-`, `.`
- **Must start/end with:** alphanumeric character

## Common kubectl Commands

```bash
# Create/Update
kubectl apply -f manifest.yaml
kubectl create -f manifest.yaml

# Get resources
kubectl get pods,svc,deploy
kubectl get all -n namespace
kubectl get pods -o wide
kubectl get pods -l app=my-app

# Describe
kubectl describe pod <name>
kubectl describe node <name>

# Logs
kubectl logs <pod>
kubectl logs <pod> -c <container>
kubectl logs -f <pod>  # Follow
kubectl logs --previous <pod>

# Execute
kubectl exec -it <pod> -- /bin/bash
kubectl exec -it <pod> -c <container> -- /bin/bash

# Port forward
kubectl port-forward pod/<name> 8080:80
kubectl port-forward svc/<name> 8080:80

# Scale
kubectl scale deployment/<name> --replicas=5

# Rollout
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>
kubectl rollout restart deployment/<name>

# Delete
kubectl delete -f manifest.yaml
kubectl delete pod <name>
kubectl delete pods -l app=my-app
```
